"""
Streamlit Frontend with VISUAL Traffic Simulation
Shows actual vehicle movement on an intersection canvas
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
    page_title="Smart Traffic Controller - Visual",
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
    .vehicle-canvas {
        background-color: #2d3436;
        border: 3px solid #0984e3;
        border-radius: 10px;
        padding: 20px;
        height: 600px;
        position: relative;
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

# ==================== INTERSECTION VISUALIZATION ====================

def create_intersection_view(state):
    """Create animated intersection with moving vehicles"""
    
    if not state:
        return go.Figure()
    
    # Create figure
    fig = go.Figure()
    
    # Intersection dimensions
    ROAD_WIDTH = 200
    CANVAS_WIDTH = 1400
    CANVAS_HEIGHT = 900
    
    # Draw roads (gray background)
    # Horizontal road (East-West)
    fig.add_shape(
        type="rect",
        x0=0, y0=(CANVAS_HEIGHT - ROAD_WIDTH) / 2,
        x1=CANVAS_WIDTH, y1=(CANVAS_HEIGHT + ROAD_WIDTH) / 2,
        fillcolor="gray", opacity=0.5, line=dict(width=0)
    )
    
    # Vertical road (North-South)
    fig.add_shape(
        type="rect",
        x0=(CANVAS_WIDTH - ROAD_WIDTH) / 2, y0=0,
        x1=(CANVAS_WIDTH + ROAD_WIDTH) / 2, y1=CANVAS_HEIGHT,
        fillcolor="gray", opacity=0.5, line=dict(width=0)
    )
    
    # Center intersection (darker)
    fig.add_shape(
        type="rect",
        x0=(CANVAS_WIDTH - ROAD_WIDTH) / 2, y0=(CANVAS_HEIGHT - ROAD_WIDTH) / 2,
        x1=(CANVAS_WIDTH + ROAD_WIDTH) / 2, y1=(CANVAS_HEIGHT + ROAD_WIDTH) / 2,
        fillcolor="darkgray", opacity=0.7, line=dict(width=0)
    )
    
    # Draw lane markings
    lane_color = "yellow"
    
    # Horizontal lane markings
    for i in range(0, CANVAS_WIDTH, 50):
        fig.add_shape(
            type="line",
            x0=i, y0=CANVAS_HEIGHT / 2,
            x1=i + 30, y1=CANVAS_HEIGHT / 2,
            line=dict(color=lane_color, width=3, dash="solid")
        )
    
    # Vertical lane markings
    for i in range(0, CANVAS_HEIGHT, 50):
        fig.add_shape(
            type="line",
            x0=CANVAS_WIDTH / 2, y0=i,
            x1=CANVAS_WIDTH / 2, y1=i + 30,
            line=dict(color=lane_color, width=3, dash="solid")
        )
    
    # Draw traffic lights
    light = state['traffic_light']
    
    # North light
    ns_color = 'green' if light['north_south'] == 'green' else 'yellow' if light['north_south'] == 'yellow' else 'red'
    fig.add_trace(go.Scatter(
        x=[CANVAS_WIDTH / 2 - 50],
        y=[CANVAS_HEIGHT / 2 - ROAD_WIDTH / 2 - 30],
        mode='markers',
        marker=dict(size=30, color=ns_color, line=dict(color='black', width=3)),
        name='North Light',
        showlegend=False
    ))
    
    # South light
    fig.add_trace(go.Scatter(
        x=[CANVAS_WIDTH / 2 + 50],
        y=[CANVAS_HEIGHT / 2 + ROAD_WIDTH / 2 + 30],
        mode='markers',
        marker=dict(size=30, color=ns_color, line=dict(color='black', width=3)),
        name='South Light',
        showlegend=False
    ))
    
    # East light
    ew_color = 'green' if light['east_west'] == 'green' else 'yellow' if light['east_west'] == 'yellow' else 'red'
    fig.add_trace(go.Scatter(
        x=[CANVAS_WIDTH / 2 + ROAD_WIDTH / 2 + 30],
        y=[CANVAS_HEIGHT / 2 + 50],
        mode='markers',
        marker=dict(size=30, color=ew_color, line=dict(color='black', width=3)),
        name='East Light',
        showlegend=False
    ))
    
    # West light
    fig.add_trace(go.Scatter(
        x=[CANVAS_WIDTH / 2 - ROAD_WIDTH / 2 - 30],
        y=[CANVAS_HEIGHT / 2 - 50],
        mode='markers',
        marker=dict(size=30, color=ew_color, line=dict(color='black', width=3)),
        name='West Light',
        showlegend=False
    ))
    
    # Draw vehicles
    vehicle_colors = {
        'car': 'blue',
        'bus': 'yellow',
        'truck': 'white',
        'emergency': 'red'
    }
    
    vehicle_symbols = {
        'car': 'square',
        'bus': 'diamond',
        'truck': 'circle',
        'emergency': 'star'
    }
    
    vehicle_sizes = {
        'car': 15,
        'bus': 25,
        'truck': 20,
        'emergency': 20
    }
    
    # Group vehicles by type for better visualization
    for v_type in ['car', 'bus', 'truck', 'emergency']:
        vehicles_of_type = [v for v in state['vehicles'] if v['type'] == v_type]
        
        if vehicles_of_type:
            x_positions = [v['position']['x'] for v in vehicles_of_type]
            y_positions = [CANVAS_HEIGHT - v['position']['y'] for v in vehicles_of_type]  # Invert Y
            
            # Create hover text
            hover_texts = [
                f"ID: {v['id']}<br>"
                f"Type: {v['type'].upper()}<br>"
                f"Direction: {v['direction']}<br>"
                f"Wait Time: {v['wait_time']:.1f}s<br>"
                f"Status: {'WAITING' if v['waiting'] else 'MOVING'}"
                for v in vehicles_of_type
            ]
            
            # Different appearance for waiting vs moving
            colors = [vehicle_colors[v_type] if not v['waiting'] else 'orange' for v in vehicles_of_type]
            
            fig.add_trace(go.Scatter(
                x=x_positions,
                y=y_positions,
                mode='markers+text',
                marker=dict(
                    size=vehicle_sizes[v_type],
                    color=colors,
                    symbol=vehicle_symbols[v_type],
                    line=dict(color='black', width=2),
                    opacity=0.9
                ),
                text=[v['id'] for v in vehicles_of_type],
                textposition='middle center',
                textfont=dict(size=8, color='white', family='Arial Black'),
                hovertext=hover_texts,
                hoverinfo='text',
                name=f"{v_type.capitalize()}s",
                showlegend=True
            ))
    
    # Direction arrows
    arrow_positions = {
        'north': (CANVAS_WIDTH / 2 - 30, 50, "⬆"),
        'south': (CANVAS_WIDTH / 2 + 30, CANVAS_HEIGHT - 50, "⬇"),
        'east': (CANVAS_WIDTH - 50, CANVAS_HEIGHT / 2 - 30, "➡"),
        'west': (50, CANVAS_HEIGHT / 2 + 30, "⬅")
    }
    
    for direction, (x, y, arrow) in arrow_positions.items():
        fig.add_annotation(
            x=x, y=y,
            text=arrow,
            font=dict(size=40, color='white'),
            showarrow=False
        )
    
    # Update layout
    fig.update_layout(
        width=CANVAS_WIDTH,
        height=CANVAS_HEIGHT,
        xaxis=dict(
            range=[0, CANVAS_WIDTH],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        yaxis=dict(
            range=[0, CANVAS_HEIGHT],
            showgrid=False,
            zeroline=False,
            showticklabels=False
        ),
        plot_bgcolor='#34495e',
        paper_bgcolor='#2d3436',
        showlegend=True,
        legend=dict(
            x=1.02,
            y=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='black',
            borderwidth=2
        ),
        hovermode='closest',
        margin=dict(l=10, r=150, t=10, b=10)
    )
    
    return fig

# ==================== INITIALIZATION ====================

if 'simulation_running' not in st.session_state:
    st.session_state.simulation_running = False
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False  # Disabled by default - enable to see animation

# ==================== HEADER ====================

st.markdown('<h1 class="main-header">🚦 SMART TRAFFIC CONTROLLER - VISUAL SIMULATION</h1>', unsafe_allow_html=True)
st.markdown("### Real-Time Vehicle Movement Visualization")
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
    st.info("💡 **Enable this to see vehicles move in real-time!**")
    auto_refresh = st.checkbox("Enable Auto-Refresh (for animation)", value=st.session_state.auto_refresh)
    if auto_refresh != st.session_state.auto_refresh:
        st.session_state.auto_refresh = auto_refresh
    
    if st.session_state.auto_refresh:
        refresh_interval = st.slider("Refresh Interval (s)", 0.5, 5.0, 1.0, 0.5)
        st.success("✅ Auto-refresh is ON - You'll see live movement!")
    
    st.markdown("---")
    
    # Legend
    st.subheader("🎨 Vehicle Legend")
    st.markdown("""
    - 🔵 **Square**: Car (Blue/Orange)
    - 🟡 **Diamond**: Bus (Yellow/Orange)
    - ⚪ **Circle**: Truck (White/Orange)
    - 🔴 **Star**: Emergency (Red)
    
    **Orange** = Vehicle is waiting
    **Original color** = Vehicle is moving
    """)

# ==================== MAIN CONTENT ====================

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
    
    # Main visualization
    st.subheader("🚦 Live Intersection View")
    
    # Emergency mode warning
    if state['traffic_light'].get('emergency_mode'):
        st.error("🚨 EMERGENCY MODE ACTIVE - Priority given to emergency vehicle!")
    
    # Create and display intersection
    intersection_fig = create_intersection_view(state)
    st.plotly_chart(intersection_fig, use_container_width=True, key=f"intersection_{state['sim_time']}")
    
    st.markdown("---")
    
    # Additional info
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚦 Traffic Light Status")
        light = state['traffic_light']
        
        st.info(f"""
        **North-South**: {light['north_south'].upper()} 🚦
        
        **East-West**: {light['east_west'].upper()} 🚦
        
        **Time Remaining**: {light.get('time_remaining', 0):.1f}s ⏱️
        """)
    
    with col2:
        st.subheader("🤖 Agent Decision")
        st.success(f"**Current Decision:**\n\n{state.get('agent_decision', 'N/A')}")
    
    # Queue lengths
    st.subheader("📊 Queue Lengths by Direction")
    
    col1, col2, col3, col4 = st.columns(4)
    
    directions = ['north', 'south', 'east', 'west']
    icons = ['⬆️', '⬇️', '➡️', '⬅️']
    
    for col, direction, icon in zip([col1, col2, col3, col4], directions, icons):
        with col:
            queue_length = metrics.get(f'queue_{direction}', 0)
            st.metric(
                f"{icon} {direction.capitalize()}",
                queue_length
            )
            progress = min(queue_length / 15, 1.0)
            st.progress(progress)

else:
    st.warning("⚠️ No simulation data available. Start the simulation to see live visualization.")
    
    # Show instruction
    st.info("""
    ### 🎬 How to Start:
    
    1. Click **▶️ Start** in the sidebar
    2. Watch vehicles spawn and move through the intersection
    3. See the AI agent make real-time decisions
    4. Try spawning an **🚑 Emergency Vehicle** to see priority routing!
    
    ### 🎨 What You'll See:
    
    - **Moving vehicles** represented by colored shapes
    - **Traffic lights** changing in real-time
    - **Queue formation** at red lights
    - **Dynamic routing** based on AI decisions
    - **Emergency mode** activation with priority handling
    """)

# ==================== AUTO-REFRESH ====================

if st.session_state.auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

# ==================== FOOTER ====================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; padding: 1rem;'>
    <p>🚦 Smart Traffic Light Controller - Visual Simulation</p>
    <p>Real-Time Vehicle Movement & AI Decision Making</p>
</div>
""", unsafe_allow_html=True)
