"""
FastAPI Backend for Smart Traffic Light Controller
Provides REST API for simulation control and data analytics
"""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio
import json
from collections import deque
import random
import time

app = FastAPI(title="Smart Traffic API", version="1.0.0")

# CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATA MODELS ====================

class VehicleModel(BaseModel):
    id: int
    type: str
    direction: str
    position: Dict[str, float]
    waiting: bool
    wait_time: float
    crossed: bool
    priority: int

class TrafficLightModel(BaseModel):
    north_south: str
    east_west: str
    time_remaining: float
    emergency_mode: bool

class SimulationState(BaseModel):
    sim_time: float
    vehicles: List[VehicleModel]
    traffic_light: TrafficLightModel
    agent_decision: str
    metrics: Dict

class SimulationConfig(BaseModel):
    spawn_rate: float = 2.0
    max_vehicles: int = 80
    green_time: int = 30
    queue_threshold: int = 10
    wait_threshold: int = 60

class AnalyticsQuery(BaseModel):
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metric: str = "all"

# ==================== SIMULATION ENGINE ====================

class SimulationEngine:
    """Lightweight simulation engine for backend"""
    
    def __init__(self):
        self.vehicles = []
        self.vehicle_count = 0
        self.sim_time = 0
        self.running = False
        self.paused = False
        
        self.config = SimulationConfig()
        
        # Traffic light state
        self.light_state = {
            'north_south': 'green',
            'east_west': 'red',
            'timer': 0,
            'phase_duration': 30,
            'emergency_mode': False
        }
        
        # Agent state
        self.agent_decision = "Initializing..."
        self.decision_history = deque(maxlen=100)
        
        # Data storage
        self.data_log = []
        self.metrics_history = deque(maxlen=1000)
        
    def spawn_vehicle(self):
        """Spawn new vehicle"""
        if len(self.vehicles) >= self.config.max_vehicles:
            return
        
        self.vehicle_count += 1
        
        # Random type
        rand = random.random()
        if rand < 0.05:
            v_type, priority = 'emergency', 10
        elif rand < 0.20:
            v_type, priority = 'bus', 2
        elif rand < 0.35:
            v_type, priority = 'truck', 1
        else:
            v_type, priority = 'car', 1
        
        direction = random.choice(['north', 'south', 'east', 'west'])
        
        vehicle = {
            'id': self.vehicle_count,
            'type': v_type,
            'direction': direction,
            'position': self._get_spawn_position(direction),
            'waiting': False,
            'wait_time': 0,
            'crossed': False,
            'priority': priority,
            'spawn_time': self.sim_time
        }
        
        self.vehicles.append(vehicle)
    
    def _get_spawn_position(self, direction):
        """Get spawn position based on direction"""
        positions = {
            'north': {'x': 700, 'y': 900},
            'south': {'x': 700, 'y': 0},
            'east': {'x': 0, 'y': 450},
            'west': {'x': 1400, 'y': 450}
        }
        return positions[direction]
    
    def perceive_environment(self):
        """Agent perception"""
        queues = {'north': [], 'south': [], 'east': [], 'west': []}
        emergency_present = False
        emergency_dir = None
        
        for v in self.vehicles:
            if not v['crossed']:
                queues[v['direction']].append(v)
                if v['type'] == 'emergency' and v['waiting']:
                    emergency_present = True
                    emergency_dir = v['direction']
        
        queue_lengths = {d: len(queues[d]) for d in queues}
        avg_wait_times = {}
        
        for d in queues:
            if queues[d]:
                avg_wait_times[d] = sum(v['wait_time'] for v in queues[d]) / len(queues[d])
            else:
                avg_wait_times[d] = 0
        
        return {
            'queues': queue_lengths,
            'wait_times': avg_wait_times,
            'emergency': emergency_present,
            'emergency_dir': emergency_dir
        }
    
    def agent_decide(self, perception):
        """Rule-based agent decision"""
        decision_info = {
            'timestamp': self.sim_time,
            'type': 'standard',
            'action': None,
            'reason': None
        }
        
        # Rule 1: Emergency vehicle priority
        if perception['emergency']:
            self.activate_emergency(perception['emergency_dir'])
            self.agent_decision = f"EMERGENCY: Green for {perception['emergency_dir']}"
            decision_info.update({
                'type': 'emergency',
                'action': f"green_{perception['emergency_dir']}",
                'reason': 'Emergency vehicle detected'
            })
            self.decision_history.append(decision_info)
            return
        
        if self.light_state['emergency_mode'] and not perception['emergency']:
            self.deactivate_emergency()
        
        # Rule 2: High queue - extend green
        for direction in perception['queues']:
            if perception['queues'][direction] > self.config.queue_threshold:
                if self.can_go(direction):
                    self.light_state['phase_duration'] += 10
                    self.agent_decision = f"Extending green for {direction} (+10s) - Queue: {perception['queues'][direction]}"
                    decision_info.update({
                        'type': 'queue_extend',
                        'action': 'extend_10s',
                        'reason': f"High queue in {direction}: {perception['queues'][direction]} vehicles"
                    })
                    self.decision_history.append(decision_info)
                    return
        
        # Rule 3: Long wait time - extend green
        for direction in perception['wait_times']:
            if perception['wait_times'][direction] > self.config.wait_threshold:
                if self.can_go(direction):
                    self.light_state['phase_duration'] += 5
                    self.agent_decision = f"Extending green for {direction} (+5s) - Wait: {perception['wait_times'][direction]:.1f}s"
                    decision_info.update({
                        'type': 'wait_extend',
                        'action': 'extend_5s',
                        'reason': f"Long wait in {direction}: {perception['wait_times'][direction]:.1f}s"
                    })
                    self.decision_history.append(decision_info)
                    return
        
        self.agent_decision = "Standard timing"
        decision_info.update({
            'type': 'standard',
            'action': 'maintain',
            'reason': 'Normal traffic conditions'
        })
        self.decision_history.append(decision_info)
    
    def activate_emergency(self, direction):
        """Activate emergency mode"""
        self.light_state['emergency_mode'] = True
        if direction in ['north', 'south']:
            self.light_state['north_south'] = 'green'
            self.light_state['east_west'] = 'red'
        else:
            self.light_state['east_west'] = 'green'
            self.light_state['north_south'] = 'red'
    
    def deactivate_emergency(self):
        """Deactivate emergency mode"""
        self.light_state['emergency_mode'] = False
        self.light_state['timer'] = 0
    
    def can_go(self, direction):
        """Check if vehicle can proceed"""
        if direction in ['north', 'south']:
            return self.light_state['north_south'] == 'green'
        else:
            return self.light_state['east_west'] == 'green'
    
    def update_light(self, dt):
        """Update traffic light state"""
        if self.light_state['emergency_mode']:
            return
        
        self.light_state['timer'] += dt
        
        if self.light_state['timer'] >= self.light_state['phase_duration']:
            self.light_state['timer'] = 0
            self.transition_light()
    
    def transition_light(self):
        """Transition between light states"""
        if self.light_state['north_south'] == 'green':
            self.light_state['north_south'] = 'yellow'
            self.light_state['phase_duration'] = 5
        elif self.light_state['north_south'] == 'yellow':
            self.light_state['north_south'] = 'red'
            self.light_state['east_west'] = 'green'
            self.light_state['phase_duration'] = 30
        elif self.light_state['east_west'] == 'green':
            self.light_state['east_west'] = 'yellow'
            self.light_state['phase_duration'] = 5
        elif self.light_state['east_west'] == 'yellow':
            self.light_state['east_west'] = 'red'
            self.light_state['north_south'] = 'green'
            self.light_state['phase_duration'] = 30
    
    def update(self, dt):
        """Update simulation step"""
        if self.paused:
            return
        
        self.sim_time += dt
        
        # Spawn vehicles
        if random.random() < dt / self.config.spawn_rate:
            self.spawn_vehicle()
        
        # Agent perception and decision
        perception = self.perceive_environment()
        self.agent_decide(perception)
        
        # Update light
        self.update_light(dt)
        
        # Update vehicles
        for vehicle in self.vehicles:
            if vehicle['crossed']:
                continue
            
            can_go = self.can_go(vehicle['direction'])
            
            # Simple distance check
            if not can_go:
                vehicle['waiting'] = True
                vehicle['wait_time'] += dt
            else:
                vehicle['waiting'] = False
                # Move vehicle
                if vehicle['direction'] == 'north':
                    vehicle['position']['y'] -= 2 * dt * 60
                elif vehicle['direction'] == 'south':
                    vehicle['position']['y'] += 2 * dt * 60
                elif vehicle['direction'] == 'east':
                    vehicle['position']['x'] += 2 * dt * 60
                elif vehicle['direction'] == 'west':
                    vehicle['position']['x'] -= 2 * dt * 60
                
                # Check if crossed
                if (vehicle['position']['y'] < -50 or vehicle['position']['y'] > 950 or
                    vehicle['position']['x'] < -50 or vehicle['position']['x'] > 1450):
                    vehicle['crossed'] = True
        
        # Log metrics
        self.log_metrics()
    
    def log_metrics(self):
        """Log current metrics"""
        active_vehicles = [v for v in self.vehicles if not v['crossed']]
        
        queues = {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        for v in active_vehicles:
            queues[v['direction']] += 1
        
        total_wait = sum(v['wait_time'] for v in active_vehicles)
        avg_wait = total_wait / len(active_vehicles) if active_vehicles else 0
        
        metrics = {
            'timestamp': self.sim_time,
            'active_vehicles': len(active_vehicles),
            'total_processed': self.vehicle_count,
            'crossed': self.vehicle_count - len(active_vehicles),
            'queue_north': queues['north'],
            'queue_south': queues['south'],
            'queue_east': queues['east'],
            'queue_west': queues['west'],
            'avg_wait_time': avg_wait,
            'light_ns': self.light_state['north_south'],
            'light_ew': self.light_state['east_west'],
            'emergency_active': self.light_state['emergency_mode']
        }
        
        self.metrics_history.append(metrics)
        self.data_log.append(metrics)
    
    def get_state(self):
        """Get current simulation state"""
        return SimulationState(
            sim_time=self.sim_time,
            vehicles=[VehicleModel(**v) for v in self.vehicles if not v['crossed']],
            traffic_light=TrafficLightModel(
                north_south=self.light_state['north_south'],
                east_west=self.light_state['east_west'],
                time_remaining=self.light_state['phase_duration'] - self.light_state['timer'],
                emergency_mode=self.light_state['emergency_mode']
            ),
            agent_decision=self.agent_decision,
            metrics=list(self.metrics_history)[-1] if self.metrics_history else {}
        )

# ==================== GLOBAL SIMULATION INSTANCE ====================

simulation = SimulationEngine()
simulation_task = None

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "Smart Traffic Light API",
        "version": "1.0.0"
    }

@app.post("/simulation/start")
async def start_simulation(background_tasks: BackgroundTasks):
    """Start the simulation"""
    global simulation_task
    
    if simulation.running:
        raise HTTPException(status_code=400, detail="Simulation already running")
    
    simulation.running = True
    background_tasks.add_task(run_simulation_loop)
    
    return {
        "status": "started",
        "sim_time": simulation.sim_time
    }

@app.post("/simulation/pause")
async def pause_simulation():
    """Pause the simulation"""
    simulation.paused = True
    return {"status": "paused"}

@app.post("/simulation/resume")
async def resume_simulation():
    """Resume the simulation"""
    simulation.paused = False
    return {"status": "resumed"}

@app.post("/simulation/stop")
async def stop_simulation():
    """Stop the simulation"""
    simulation.running = False
    return {
        "status": "stopped",
        "total_vehicles": simulation.vehicle_count,
        "sim_time": simulation.sim_time
    }

@app.post("/simulation/reset")
async def reset_simulation():
    """Reset the simulation"""
    global simulation
    simulation = SimulationEngine()
    return {"status": "reset"}

@app.get("/simulation/state")
async def get_state():
    """Get current simulation state"""
    return simulation.get_state()

@app.get("/simulation/config")
async def get_config():
    """Get simulation configuration"""
    return simulation.config

@app.put("/simulation/config")
async def update_config(config: SimulationConfig):
    """Update simulation configuration"""
    simulation.config = config
    return {"status": "updated", "config": config}

@app.post("/simulation/spawn_emergency")
async def spawn_emergency():
    """Spawn an emergency vehicle"""
    simulation.vehicle_count += 1
    direction = random.choice(['north', 'south', 'east', 'west'])
    
    vehicle = {
        'id': simulation.vehicle_count,
        'type': 'emergency',
        'direction': direction,
        'position': simulation._get_spawn_position(direction),
        'waiting': False,
        'wait_time': 0,
        'crossed': False,
        'priority': 10,
        'spawn_time': simulation.sim_time
    }
    
    simulation.vehicles.append(vehicle)
    
    return {
        "status": "spawned",
        "vehicle_id": vehicle['id'],
        "direction": direction
    }

# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary"""
    if not simulation.data_log:
        return {"error": "No data available"}
    
    df = pd.DataFrame(simulation.data_log)
    
    summary = {
        "total_vehicles_processed": int(df['total_processed'].max()),
        "total_simulation_time": float(df['timestamp'].max()),
        "average_wait_time": float(df['avg_wait_time'].mean()),
        "max_wait_time": float(df['avg_wait_time'].max()),
        "average_queue_length": {
            "north": float(df['queue_north'].mean()),
            "south": float(df['queue_south'].mean()),
            "east": float(df['queue_east'].mean()),
            "west": float(df['queue_west'].mean())
        },
        "peak_queue_length": int(df[['queue_north', 'queue_south', 'queue_east', 'queue_west']].max().max()),
        "emergency_activations": int(df['emergency_active'].sum()),
        "throughput": float(df['crossed'].max() / (df['timestamp'].max() / 60)) if df['timestamp'].max() > 0 else 0
    }
    
    return summary

@app.get("/analytics/timeseries")
async def get_timeseries(metric: str = "all"):
    """Get time series data"""
    if not simulation.data_log:
        return {"error": "No data available"}
    
    df = pd.DataFrame(simulation.data_log)
    
    if metric == "all":
        return df.to_dict('records')
    elif metric in df.columns:
        return df[['timestamp', metric]].to_dict('records')
    else:
        raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")

@app.get("/analytics/agent_decisions")
async def get_agent_decisions():
    """Get agent decision history"""
    return {
        "total_decisions": len(simulation.decision_history),
        "decisions": list(simulation.decision_history)
    }

@app.get("/analytics/vehicle_stats")
async def get_vehicle_stats():
    """Get vehicle statistics"""
    if not simulation.vehicles:
        return {"error": "No vehicles"}
    
    types = {'car': 0, 'bus': 0, 'truck': 0, 'emergency': 0}
    directions = {'north': 0, 'south': 0, 'east': 0, 'west': 0}
    
    for v in simulation.vehicles:
        types[v['type']] += 1
        directions[v['direction']] += 1
    
    return {
        "by_type": types,
        "by_direction": directions,
        "total": len(simulation.vehicles),
        "active": len([v for v in simulation.vehicles if not v['crossed']]),
        "crossed": len([v for v in simulation.vehicles if v['crossed']])
    }

# ==================== WEBSOCKET FOR REAL-TIME UPDATES ====================

@app.websocket("/ws/simulation")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time simulation updates"""
    await websocket.accept()
    
    try:
        while True:
            if simulation.running:
                state = simulation.get_state()
                await websocket.send_json(state.dict())
            
            await asyncio.sleep(0.1)  # 10 updates per second
    except Exception as e:
        print(f"WebSocket error: {e}")

# ==================== BACKGROUND TASK ====================

async def run_simulation_loop():
    """Background task to run simulation"""
    dt = 0.1  # 100ms timestep
    
    while simulation.running:
        if not simulation.paused:
            simulation.update(dt)
        
        await asyncio.sleep(dt)

# ==================== STARTUP EVENT ====================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("Smart Traffic Light API started")
    print("Docs available at: http://localhost:8000/docs")