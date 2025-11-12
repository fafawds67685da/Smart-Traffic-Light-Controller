"""
Streamlit Frontend for Smart Traffic Light Controller
Interactive dashboard with real-time visualization and analytics
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import json
from datetime import datetime

# ==================== CONFIGURATION ====================

API_BASE_URL = "http://localhost:8000"
st.set_page_config(
    page_title="Smart Traffic Controller",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B35;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FF6B35;
    }
    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .status-running {
        background-color: #28a745;
        color: white;
    }
    .status-paused {
        background-color: #ffc107;
        color: black;
    }
    .status-stopped {
        background-color: #dc3545;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==================== API HELPERS ====================

def api_call(endpoint, method="GET", data=None):
    """Make API call with error handling"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

def get_simulation_state():
    """Get current simulation state"""
    return api_call("/simulation/state")

def get_analytics_summary():
    """Get analytics summary"""
    return api_call("/analytics/summary")

def get_timeseries():
    """Get time series data"""
    return api_call("/analytics/timeseries")

def get_agent_decisions():
    """Get agent decision history"""
    return api_call("/analytics/agent_decisions")

def get_vehicle_stats():
    """Get vehicle statistics"""
    return api_call("/analytics/vehicle_stats")

# ==================== INITIALIZATION ====================

if 'simulation_running' not in st.session_state:
    st.session_state.simulation_running = False
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False  # Changed to False - user can enable manually

# ==================== HEADER ====================

st.markdown('<h1 class="main-header">🚦 SMART TRAFFIC LIGHT CONTROLLER</h1>', unsafe_allow_html=True)
st.markdown("### AI-Powered Traffic Management System")
st.markdown("---")

# ==================== SIDEBAR CONTROLS ====================

with st.sidebar:
    st.header("🎮 Control Panel")
    
    # Simulation controls
    st.subheader("Simulation Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start", use_container_width=True):
            result = api_call("/simulation/start", "POST")
            if result:
                st.session_state.simulation_running = True
                st.success("Simulation started!")
    
    with col2:
        if st.button("⏹️ Stop", use_container_width=True):
            result = api_call("/simulation/stop", "POST")
            if result:
                st.session_state.simulation_running = False
                st.success("Simulation stopped!")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("⏸️ Pause", use_container_width=True):
            result = api_call("/simulation/pause", "POST")
            if result:
                st.info("Simulation paused")
    
    with col4:
        if st.button("▶️ Resume", use_container_width=True):
            result = api_call("/simulation/resume", "POST")
            if result:
                st.info("Simulation resumed")
    
    if st.button("🔄 Reset", use_container_width=True):
        result = api_call("/simulation/reset", "POST")
        if result:
            st.session_state.simulation_running = False
            st.success("Simulation reset!")
    
    st.markdown("---")
    
    # Emergency controls
    st.subheader("🚨 Emergency Controls")
    if st.button("🚑 Spawn Emergency Vehicle", use_container_width=True):
        result = api_call("/simulation/spawn_emergency", "POST")
        if result:
            st.warning(f"Emergency vehicle spawned from {result['direction']}")
    
    st.markdown("---")
    
    # Configuration
    st.subheader("⚙️ Configuration")
    
    spawn_rate = st.slider("Vehicle Spawn Rate (s)", 0.5, 5.0, 2.0, 0.5)
    max_vehicles = st.slider("Max Vehicles", 20, 150, 80, 10)
    green_time = st.slider("Green Light Duration (s)", 15, 60, 30, 5)
    
    if st.button("Apply Config", use_container_width=True):
        config = {
            "spawn_rate": spawn_rate,
            "max_vehicles": max_vehicles,
            "green_time": green_time,
            "queue_threshold": 10,
            "wait_threshold": 60
        }
        result = api_call("/simulation/config", "PUT", config)
        if result:
            st.success("Configuration updated!")
    
    st.markdown("---")
    
    # Auto-refresh
    st.subheader("🔄 Auto Refresh")
    st.warning("⚠️ Auto-refresh will reload the page continuously")
    auto_refresh = st.checkbox("Enable Auto-Refresh (Not Recommended)", value=st.session_state.auto_refresh)
    if auto_refresh != st.session_state.auto_refresh:
        st.session_state.auto_refresh = auto_refresh
    
    if st.session_state.auto_refresh:
        refresh_interval = st.slider("Refresh Interval (s)", 1, 10, 2)
    
    st.info("💡 Click 'Start' to begin simulation. Manually refresh to see updates.")

# ==================== MAIN CONTENT ====================

# Tab navigation
tab1, tab2, tab3, tab4 = st.tabs(["📊 Live Dashboard", "📈 Analytics", "🤖 Agent Insights", "📚 Documentation"])

# ==================== TAB 1: LIVE DASHBOARD ====================

with tab1:
    # Get current state
    state = get_simulation_state()
    
    if state:
        # Status row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("⏱️ Simulation Time", f"{state['sim_time']:.1f}s")
        
        with col2:
            metrics = state.get('metrics', {})
            st.metric("🚗 Active Vehicles", metrics.get('active_vehicles', 0))
        
        with col3:
            st.metric("✅ Crossed", metrics.get('crossed', 0))
        
        with col4:
            st.metric("⏳ Avg Wait Time", f"{metrics.get('avg_wait_time', 0):.1f}s")
        
        st.markdown("---")
        
        # Main visualization row
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🚦 Traffic Light Status")
            
            # Traffic light visualization
            light = state['traffic_light']
            
            fig = go.Figure()
            
            # North-South light
            ns_color = 'green' if light['north_south'] == 'green' else 'yellow' if light['north_south'] == 'yellow' else 'red'
            fig.add_trace(go.Scatter(
                x=[0], y=[1],
                mode='markers+text',
                marker=dict(size=80, color=ns_color, line=dict(color='black', width=2)),
                text=['N-S'],
                textposition='middle center',
                textfont=dict(size=20, color='black'),
                name='North-South'
            ))
            
            # East-West light
            ew_color = 'green' if light['east_west'] == 'green' else 'yellow' if light['east_west'] == 'yellow' else 'red'
            fig.add_trace(go.Scatter(
                x=[1], y=[1],
                mode='markers+text',
                marker=dict(size=80, color=ew_color, line=dict(color='black', width=2)),
                text=['E-W'],
                textposition='middle center',
                textfont=dict(size=20, color='black'),
                name='East-West'
            ))
            
            fig.update_layout(
                showlegend=False,
                height=250,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.5, 1.5]),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0.5, 1.5]),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Time remaining
            if light.get('emergency_mode'):
                st.error("🚨 EMERGENCY MODE ACTIVE")
            else:
                st.info(f"⏱️ Time Remaining: {light.get('time_remaining', 0):.1f}s")
        
        with col2:
            st.subheader("🚗 Vehicle Types")
            
            vehicle_stats = get_vehicle_stats()
            if vehicle_stats and 'by_type' in vehicle_stats:
                types_df = pd.DataFrame([
                    {"Type": "🚗 Car", "Count": vehicle_stats['by_type']['car'], "Color": "🔵"},
                    {"Type": "🚌 Bus", "Count": vehicle_stats['by_type']['bus'], "Color": "🟡"},
                    {"Type": "🚚 Truck", "Count": vehicle_stats['by_type']['truck'], "Color": "⚪"},
                    {"Type": "🚑 Emergency", "Count": vehicle_stats['by_type']['emergency'], "Color": "🔴"}
                ])
                
                st.dataframe(types_df, hide_index=True, use_container_width=True)
        
        st.markdown("---")
        
        # Queue lengths
        st.subheader("📊 Queue Lengths by Direction")
        
        col1, col2, col3, col4 = st.columns(4)
        
        directions = ['north', 'south', 'east', 'west']
        icons = ['⬆️', '⬇️', '➡️', '⬅️']
        
        for col, direction, icon in zip([col1, col2, col3, col4], directions, icons):
            with col:
                queue_length = metrics.get(f'queue_{direction}', 0)
                color = "🔴" if queue_length > 8 else "🟡" if queue_length > 5 else "🟢"
                st.metric(
                    f"{icon} {direction.capitalize()}",
                    queue_length,
                    delta=None
                )
                # Progress bar
                progress = min(queue_length / 15, 1.0)
                st.progress(progress)
        
        st.markdown("---")
        
        # Agent decision
        st.subheader("🤖 Agent Decision")
        st.info(f"**Current Decision:** {state.get('agent_decision', 'N/A')}")
    
    else:
        st.warning("⚠️ No simulation data available. Start the simulation to see live data.")

# ==================== TAB 2: ANALYTICS ====================

with tab2:
    st.header("📈 Traffic Analytics & Statistics")
    
    summary = get_analytics_summary()
    
    if summary and 'error' not in summary:
        # Summary metrics
        st.subheader("📊 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Vehicles",
                summary['total_vehicles_processed'],
                help="Total number of vehicles spawned"
            )
        
        with col2:
            st.metric(
                "Throughput",
                f"{summary['throughput']:.2f}/min",
                help="Vehicles processed per minute"
            )
        
        with col3:
            st.metric(
                "Avg Wait Time",
                f"{summary['average_wait_time']:.2f}s",
                help="Average waiting time across all vehicles"
            )
        
        with col4:
            st.metric(
                "Emergency Calls",
                summary['emergency_activations'],
                help="Number of emergency vehicle activations"
            )
        
        st.markdown("---")
        
        # Time series data
        timeseries = get_timeseries()
        
        if timeseries and isinstance(timeseries, list) and len(timeseries) > 0:
            df = pd.DataFrame(timeseries)
            
            # Wait time over time
            st.subheader("⏱️ Average Wait Time Over Time")
            fig = px.line(
                df, x='timestamp', y='avg_wait_time',
                title="Average Wait Time Evolution",
                labels={'timestamp': 'Time (s)', 'avg_wait_time': 'Wait Time (s)'}
            )
            fig.update_traces(line_color='#FF6B35')
            st.plotly_chart(fig, use_container_width=True)
            
            # Queue lengths comparison
            st.subheader("📊 Queue Lengths Comparison")
            
            fig = make_subplots(rows=2, cols=2,
                              subplot_titles=('North', 'South', 'East', 'West'))
            
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['queue_north'],
                                    name='North', line=dict(color='blue')),
                         row=1, col=1)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['queue_south'],
                                    name='South', line=dict(color='green')),
                         row=1, col=2)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['queue_east'],
                                    name='East', line=dict(color='red')),
                         row=2, col=1)
            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['queue_west'],
                                    name='West', line=dict(color='orange')),
                         row=2, col=2)
            
            fig.update_layout(height=600, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Heatmap of queue distribution
            st.subheader("🔥 Queue Distribution Heatmap")
            
            heatmap_data = df[['queue_north', 'queue_south', 'queue_east', 'queue_west']].T
            
            fig = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=df['timestamp'],
                y=['North', 'South', 'East', 'West'],
                colorscale='RdYlGn_r',
                colorbar=dict(title="Queue Length")
            ))
            
            fig.update_layout(
                title="Queue Length Distribution Over Time",
                xaxis_title="Time (s)",
                yaxis_title="Direction",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistics table
            st.subheader("📋 Detailed Statistics")
            
            stats_df = pd.DataFrame({
                'Direction': ['North', 'South', 'East', 'West'],
                'Avg Queue': [
                    summary['average_queue_length']['north'],
                    summary['average_queue_length']['south'],
                    summary['average_queue_length']['east'],
                    summary['average_queue_length']['west']
                ],
                'Peak Queue': [
                    df['queue_north'].max(),
                    df['queue_south'].max(),
                    df['queue_east'].max(),
                    df['queue_west'].max()
                ]
            })
            
            st.dataframe(stats_df, hide_index=True, use_container_width=True)
    
    else:
        st.warning("⚠️ No analytics data available. Run the simulation to collect data.")

# ==================== TAB 3: AGENT INSIGHTS ====================

with tab3:
    st.header("🤖 Intelligent Agent Decision Analysis")
    
    st.markdown("""
    ### Agent Architecture
    
    The traffic controller uses a **Rule-Based Intelligent Agent** with the following components:
    
    1. **Perception**: Monitors queue lengths, wait times, and emergency vehicles
    2. **Decision Making**: Applies prioritized rules to optimize traffic flow
    3. **Action**: Adjusts traffic light timing dynamically
    """)
    
    # Decision rules
    st.subheader("📜 Agent Rules (Priority Order)")
    
    rules_df = pd.DataFrame([
        {
            "Priority": 1,
            "Rule": "Emergency Vehicle Detection",
            "Condition": "Emergency vehicle waiting",
            "Action": "Immediate green light for emergency direction",
            "Impact": "🚑 Life-saving priority"
        },
        {
            "Priority": 2,
            "Rule": "High Queue Extension",
            "Condition": "Queue length > 10 vehicles",
            "Action": "Extend green time by +10 seconds",
            "Impact": "📊 Reduces congestion"
        },
        {
            "Priority": 3,
            "Rule": "Long Wait Extension",
            "Condition": "Average wait > 60 seconds",
            "Action": "Extend green time by +5 seconds",
            "Impact": "⏱️ Improves wait times"
        },
        {
            "Priority": 4,
            "Rule": "Standard Timing",
            "Condition": "Normal conditions",
            "Action": "Maintain regular light cycles",
            "Impact": "⚖️ Balanced flow"
        }
    ])
    
    st.dataframe(rules_df, hide_index=True, use_container_width=True)
    
    st.markdown("---")
    
    # Decision history
    decisions = get_agent_decisions()
    
    if decisions and 'decisions' in decisions:
        st.subheader("📊 Decision History")
        
        st.metric("Total Decisions Made", decisions['total_decisions'])
        
        if len(decisions['decisions']) > 0:
            # Convert to DataFrame
            dec_df = pd.DataFrame(decisions['decisions'])
            
            # Decision type distribution
            if 'type' in dec_df.columns:
                type_counts = dec_df['type'].value_counts()
                
                fig = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="Decision Type Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent decisions
            st.subheader("🕐 Recent Decisions")
            
            recent = dec_df.tail(10).sort_values('timestamp', ascending=False)
            st.dataframe(recent[['timestamp', 'type', 'action', 'reason']], hide_index=True, use_container_width=True)
    
    else:
        st.info("No decision history available yet.")

# ==================== TAB 4: DOCUMENTATION ====================

with tab4:
    st.header("📚 System Documentation")
    
    st.markdown("""
    ## 🚦 Smart Traffic Light Controller
    
    ### Overview
    
    An AI-powered traffic management system that uses intelligent agents and data science 
    to optimize traffic flow at intersections.
    
    ---
    
    ### 🤖 Agentic AI Components
    
    #### 1. Perception-Decision-Action Loop
    - **Perceive**: Monitor environment (queues, wait times, vehicle types)
    - **Decide**: Apply rule-based logic with priority handling
    - **Act**: Adjust traffic light timing dynamically
    
    #### 2. Rule-Based Intelligence
    - Emergency vehicle priority (highest)
    - Queue-based adaptive timing
    - Wait time optimization
    - Standard cycle management
    
    #### 3. Learning & Adaptation
    - Tracks decision effectiveness
    - Logs metrics for offline analysis
    - Pattern recognition for optimization
    
    ---
    
    ### 🔍 Search Algorithms
    
    #### A* Pathfinding Implementation
    
    **Algorithm**: A* (A-star) search for optimal vehicle routing
    
    **Components**:
    - **Heuristic**: Manhattan distance
    - **Cost Function**: g(n) + h(n)
    - **Open List**: Priority queue of nodes to explore
    - **Closed List**: Visited nodes
    
    **Applications**:
    - Vehicle path planning
    - Intersection navigation
    - Collision avoidance
    
    **Complexity**: O(b^d) where b=branching factor, d=depth
    
    ---
    
    ### 🚗 Vehicle Types & Color Coding
    
    | Vehicle | Color | Speed | Priority | Characteristics |
    |---------|-------|-------|----------|-----------------|
    | 🚗 Car | 🔵 Blue | 2.0 | 1 | Standard vehicle |
    | 🚌 Bus | 🟡 Yellow | 1.2 | 2 | Higher priority, larger |
    | 🚚 Truck | ⚪ Gray | 1.0 | 1 | Slow, large cargo |
    | 🚑 Emergency | 🔴 Red (Flash) | 3.5 | 10 | Highest priority |
    
    ---
    
    ### 📊 Data Science Concepts
    
    #### 1. Real-Time Data Collection
    - CSV logging with timestamps
    - Queue length tracking
    - Wait time measurements
    - Vehicle type distribution
    
    #### 2. Statistical Metrics
    - **Mean**: Average wait times
    - **Max**: Peak queue lengths
    - **Distribution**: Vehicle type frequencies
    - **Throughput**: Vehicles per minute
    
    #### 3. Time Series Analysis
    - Trend detection
    - Pattern recognition
    - Seasonal variations
    - Anomaly detection
    
    #### 4. Visualization Techniques
    - Line charts for trends
    - Heatmaps for distribution
    - Pie charts for proportions
    - Bar charts for comparisons
    
    ---
    
    ### 🏗️ System Architecture
    
    ```
    ┌─────────────────┐
    │   Streamlit     │  Frontend Dashboard
    │   Frontend      │  - Live visualization
    └────────┬────────┘  - Control interface
             │
             │ HTTP/WebSocket
             ↓
    ┌─────────────────┐
    │   FastAPI       │  Backend API
    │   Backend       │  - Simulation engine
    └────────┬────────┘  - Analytics
             │
             │
    ┌────────┴────────┐
    │  Simulation     │  Core Logic
    │  Engine         │  - Agent AI
    │                 │  - A* pathfinding
    │                 │  - Data collection
    └─────────────────┘
    ```
    
    ---
    
    ### 🔧 API Endpoints
    
    #### Simulation Control
    - `POST /simulation/start` - Start simulation
    - `POST /simulation/pause` - Pause simulation
    - `POST /simulation/resume` - Resume simulation
    - `POST /simulation/stop` - Stop simulation
    - `POST /simulation/reset` - Reset simulation
    - `GET /simulation/state` - Get current state
    
    #### Analytics
    - `GET /analytics/summary` - Get summary statistics
    - `GET /analytics/timeseries` - Get time series data
    - `GET /analytics/agent_decisions` - Get decision history
    - `GET /analytics/vehicle_stats` - Get vehicle statistics
    
    #### Configuration
    - `GET /simulation/config` - Get configuration
    - `PUT /simulation/config` - Update configuration
    - `POST /simulation/spawn_emergency` - Spawn emergency vehicle
    
    ---
    
    ### 📈 Key Performance Indicators
    
    1. **Average Wait Time**: Lower is better
    2. **Throughput**: Vehicles per minute
    3. **Queue Length**: Peak and average
    4. **Emergency Response Time**: Critical metric
    5. **Agent Decision Efficiency**: Rule utilization
    
    ---
    
    ### 🎯 Project Highlights
    
    ✅ **Intelligent Agents**: Rule-based decision making with priority handling
    
    ✅ **A* Algorithm**: Optimal pathfinding for vehicle navigation
    
    ✅ **Real-Time Data**: Live collection and streaming
    
    ✅ **Statistical Analysis**: Comprehensive metrics and KPIs
    
    ✅ **Visualization**: Interactive dashboards with Plotly
    
    ✅ **Scalable Architecture**: FastAPI backend + Streamlit frontend
    
    """)

# ==================== AUTO-REFRESH ====================

if st.session_state.auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# ==================== FOOTER ====================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 1rem;'>
    <p>🚦 Smart Traffic Light Controller | AI & Data Science Project</p>
    <p>Built with FastAPI, Streamlit, and Plotly</p>
</div>
""", unsafe_allow_html=True)