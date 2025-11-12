"""
Smart Traffic Light Controller - Main Application
A comprehensive AI and Data Science project demonstrating:
- Intelligent Agents
- A* Pathfinding Algorithm
- Real-time Data Collection
- Statistical Analysis
"""

import pygame
import random
import math
import time
import csv
import os
from collections import deque
from datetime import datetime

# ==================== CONFIGURATION ====================
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 100, 255)
ORANGE = (255, 165, 0)

# Grid for A* pathfinding
GRID_SIZE = 40
CELL_SIZE = 20

# Traffic light timing
GREEN_TIME = 30
YELLOW_TIME = 5
RED_TIME = 2

# Vehicle settings
VEHICLE_SPAWN_RATE = 2.0
MAX_VEHICLES = 80

# Agent thresholds
QUEUE_HIGH = 10
WAIT_THRESHOLD = 60

# ==================== VEHICLE CLASS ====================
class Vehicle:
    """Represents a vehicle with type, position, and behavior"""
    
    vehicle_count = 0
    
    def __init__(self, v_type, direction, lane):
        Vehicle.vehicle_count += 1
        self.id = Vehicle.vehicle_count
        self.type = v_type
        self.direction = direction
        self.lane = lane
        
        # Type-specific properties
        if v_type == 'car':
            self.speed = 2.0
            self.size = (20, 30)
            self.color = BLUE
            self.priority = 1
        elif v_type == 'bus':
            self.speed = 1.2
            self.size = (25, 45)
            self.color = YELLOW
            self.priority = 2
        elif v_type == 'truck':
            self.speed = 1.0
            self.size = (25, 50)
            self.color = GRAY
            self.priority = 1
        elif v_type == 'emergency':
            self.speed = 3.5
            self.size = (22, 35)
            self.color = RED
            self.priority = 10
        
        # Position
        self.x, self.y = self.get_spawn_position()
        self.angle = self.get_initial_angle()
        
        # State
        self.waiting = False
        self.wait_time = 0
        self.crossed = False
        self.path = []
        self.path_index = 0
        self.spawn_time = time.time()
        
    def get_spawn_position(self):
        """Get spawn position based on direction and lane"""
        lane_offset = 25 if self.lane == 0 else -25
        
        if self.direction == 'north':
            return (WINDOW_WIDTH//2 + lane_offset, WINDOW_HEIGHT)
        elif self.direction == 'south':
            return (WINDOW_WIDTH//2 - lane_offset, 0)
        elif self.direction == 'east':
            return (0, WINDOW_HEIGHT//2 - lane_offset)
        elif self.direction == 'west':
            return (WINDOW_WIDTH, WINDOW_HEIGHT//2 + lane_offset)
    
    def get_initial_angle(self):
        """Get initial rotation angle"""
        angles = {'north': 0, 'south': 180, 'east': 90, 'west': 270}
        return angles[self.direction]
    
    def update(self, dt, can_go):
        """Update vehicle position and state"""
        if self.crossed:
            return
        
        if not can_go:
            self.waiting = True
            self.wait_time += dt
            return
        
        self.waiting = False
        
        # Simple forward movement
        if self.direction == 'north':
            self.y -= self.speed
            if self.y < -50:
                self.crossed = True
        elif self.direction == 'south':
            self.y += self.speed
            if self.y > WINDOW_HEIGHT + 50:
                self.crossed = True
        elif self.direction == 'east':
            self.x += self.speed
            if self.x > WINDOW_WIDTH + 50:
                self.crossed = True
        elif self.direction == 'west':
            self.x -= self.speed
            if self.x < -50:
                self.crossed = True
    
    def draw(self, screen):
        """Draw vehicle on screen"""
        if self.crossed:
            return
        
        rect = pygame.Rect(0, 0, self.size[0], self.size[1])
        rect.center = (int(self.x), int(self.y))
        
        # Draw vehicle
        pygame.draw.rect(screen, self.color, rect, border_radius=3)
        
        # Emergency vehicle flash
        if self.type == 'emergency':
            if int(time.time() * 4) % 2 == 0:
                pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 5)

# ==================== TRAFFIC LIGHT CLASS ====================
class TrafficLight:
    """Manages traffic light state machine"""
    
    def __init__(self):
        self.states = ['green', 'yellow', 'red']
        self.current_state = {'north-south': 'green', 'east-west': 'red'}
        self.timer = 0
        self.phase_duration = GREEN_TIME
        self.emergency_mode = False
        self.emergency_direction = None
        
    def update(self, dt):
        """Update traffic light state"""
        if self.emergency_mode:
            return
        
        self.timer += dt
        
        if self.timer >= self.phase_duration:
            self.timer = 0
            self.transition()
    
    def transition(self):
        """Transition between light states"""
        if self.current_state['north-south'] == 'green':
            self.current_state['north-south'] = 'yellow'
            self.phase_duration = YELLOW_TIME
        elif self.current_state['north-south'] == 'yellow':
            self.current_state['north-south'] = 'red'
            self.current_state['east-west'] = 'green'
            self.phase_duration = GREEN_TIME
        elif self.current_state['east-west'] == 'green':
            self.current_state['east-west'] = 'yellow'
            self.phase_duration = YELLOW_TIME
        elif self.current_state['east-west'] == 'yellow':
            self.current_state['east-west'] = 'red'
            self.current_state['north-south'] = 'green'
            self.phase_duration = GREEN_TIME
    
    def can_go(self, direction):
        """Check if vehicle can proceed"""
        if direction in ['north', 'south']:
            return self.current_state['north-south'] == 'green'
        else:
            return self.current_state['east-west'] == 'green'
    
    def activate_emergency(self, direction):
        """Activate emergency mode for priority vehicle"""
        self.emergency_mode = True
        self.emergency_direction = direction
        
        if direction in ['north', 'south']:
            self.current_state['north-south'] = 'green'
            self.current_state['east-west'] = 'red'
        else:
            self.current_state['east-west'] = 'green'
            self.current_state['north-south'] = 'red'
    
    def deactivate_emergency(self):
        """Deactivate emergency mode"""
        self.emergency_mode = False
        self.emergency_direction = None
        self.timer = 0
    
    def draw(self, screen):
        """Draw traffic lights"""
        # North-South lights
        ns_color = GREEN if self.current_state['north-south'] == 'green' else \
                   YELLOW if self.current_state['north-south'] == 'yellow' else RED
        
        # East-West lights
        ew_color = GREEN if self.current_state['east-west'] == 'green' else \
                   YELLOW if self.current_state['east-west'] == 'yellow' else RED
        
        # Draw light circles
        pygame.draw.circle(screen, ns_color, (WINDOW_WIDTH//2 - 80, WINDOW_HEIGHT//2 - 100), 15)
        pygame.draw.circle(screen, ns_color, (WINDOW_WIDTH//2 + 80, WINDOW_HEIGHT//2 + 100), 15)
        pygame.draw.circle(screen, ew_color, (WINDOW_WIDTH//2 - 100, WINDOW_HEIGHT//2 + 80), 15)
        pygame.draw.circle(screen, ew_color, (WINDOW_WIDTH//2 + 100, WINDOW_HEIGHT//2 - 80), 15)

# ==================== A* PATHFINDING ====================
class AStarPathfinder:
    """Implements A* search algorithm for pathfinding"""
    
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.explored_nodes = []
        self.search_active = False
    
    def manhattan_distance(self, pos1, pos2):
        """Heuristic function: Manhattan distance"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def get_neighbors(self, pos):
        """Get valid neighboring positions"""
        x, y = pos
        neighbors = []
        
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                neighbors.append((nx, ny))
        
        return neighbors
    
    def find_path(self, start, goal):
        """Find optimal path using A* algorithm"""
        self.explored_nodes = []
        self.search_active = True
        
        open_list = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.manhattan_distance(start, goal)}
        
        while open_list:
            open_list.sort(key=lambda x: x[0])
            current_f, current = open_list.pop(0)
            
            self.explored_nodes.append(current)
            
            if current == goal:
                path = self.reconstruct_path(came_from, current)
                self.search_active = False
                return path
            
            for neighbor in self.get_neighbors(current):
                tentative_g = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.manhattan_distance(neighbor, goal)
                    
                    if not any(neighbor == node for _, node in open_list):
                        open_list.append((f_score[neighbor], neighbor))
        
        self.search_active = False
        return []
    
    def reconstruct_path(self, came_from, current):
        """Reconstruct path from goal to start"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

# ==================== INTELLIGENT AGENT ====================
class TrafficAgent:
    """Rule-based intelligent agent for traffic control"""
    
    def __init__(self, traffic_light):
        self.light = traffic_light
        self.last_decision = "Initializing..."
        self.decision_history = []
    
    def perceive(self, vehicles):
        """Perceive environment state"""
        # Count vehicles by direction
        queues = {'north': [], 'south': [], 'east': [], 'west': []}
        emergency_present = False
        emergency_dir = None
        
        for v in vehicles:
            if not v.crossed:
                queues[v.direction].append(v)
                if v.type == 'emergency' and v.waiting:
                    emergency_present = True
                    emergency_dir = v.direction
        
        # Calculate metrics
        queue_lengths = {d: len(queues[d]) for d in queues}
        avg_wait_times = {}
        
        for d in queues:
            if queues[d]:
                avg_wait_times[d] = sum(v.wait_time for v in queues[d]) / len(queues[d])
            else:
                avg_wait_times[d] = 0
        
        return {
            'queues': queue_lengths,
            'wait_times': avg_wait_times,
            'emergency': emergency_present,
            'emergency_dir': emergency_dir
        }
    
    def decide(self, perception):
        """Make intelligent decision based on rules"""
        # Rule 1: Emergency vehicle priority
        if perception['emergency']:
            self.light.activate_emergency(perception['emergency_dir'])
            decision = f"EMERGENCY: Green for {perception['emergency_dir']}"
            self.last_decision = decision
            self.decision_history.append(('emergency', time.time()))
            return
        
        # Deactivate emergency if no longer present
        if self.light.emergency_mode and not perception['emergency']:
            self.light.deactivate_emergency()
        
        # Rule 2: High queue - extend green
        for direction in perception['queues']:
            if perception['queues'][direction] > QUEUE_HIGH:
                if self.light.can_go(direction):
                    self.light.phase_duration += 10
                    decision = f"Extending green for {direction} (+10s) - Queue: {perception['queues'][direction]}"
                    self.last_decision = decision
                    self.decision_history.append(('extend_high', time.time()))
                    return
        
        # Rule 3: Long wait time - extend green
        for direction in perception['wait_times']:
            if perception['wait_times'][direction] > WAIT_THRESHOLD:
                if self.light.can_go(direction):
                    self.light.phase_duration += 5
                    decision = f"Extending green for {direction} (+5s) - Wait: {perception['wait_times'][direction]:.1f}s"
                    self.last_decision = decision
                    self.decision_history.append(('extend_wait', time.time()))
                    return
        
        self.last_decision = "Standard timing"

# ==================== DATA COLLECTOR ====================
class DataCollector:
    """Collects and logs traffic data for analysis"""
    
    def __init__(self, filename='traffic_data.csv'):
        self.filename = filename
        self.data = []
        self.create_file()
    
    def create_file(self):
        """Create CSV file with headers"""
        os.makedirs('data', exist_ok=True)
        with open(f'data/{self.filename}', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'simulation_time', 
                'queue_north', 'queue_south', 'queue_east', 'queue_west',
                'wait_north', 'wait_south', 'wait_east', 'wait_west',
                'light_ns', 'light_ew',
                'agent_decision', 'emergency_active',
                'total_vehicles', 'crossed_vehicles'
            ])
    
    def log(self, sim_time, vehicles, light, agent):
        """Log current state"""
        # Calculate metrics
        queues = {'north': [], 'south': [], 'east': [], 'west': []}
        crossed = 0
        
        for v in vehicles:
            if v.crossed:
                crossed += 1
            else:
                queues[v.direction].append(v)
        
        queue_counts = {d: len(queues[d]) for d in queues}
        wait_times = {}
        
        for d in queues:
            if queues[d]:
                wait_times[d] = sum(v.wait_time for v in queues[d]) / len(queues[d])
            else:
                wait_times[d] = 0
        
        emergency = any(v.type == 'emergency' and not v.crossed for v in vehicles)
        
        # Write to CSV
        with open(f'data/{self.filename}', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                f'{sim_time:.1f}',
                queue_counts['north'], queue_counts['south'], 
                queue_counts['east'], queue_counts['west'],
                f'{wait_times["north"]:.2f}', f'{wait_times["south"]:.2f}',
                f'{wait_times["east"]:.2f}', f'{wait_times["west"]:.2f}',
                light.current_state['north-south'],
                light.current_state['east-west'],
                agent.last_decision,
                emergency,
                len(vehicles), crossed
            ])

# ==================== MAIN SIMULATION ====================
class TrafficSimulation:
    """Main simulation controller"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Smart Traffic Light Controller")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        
        # Initialize components
        self.traffic_light = TrafficLight()
        self.agent = TrafficAgent(self.traffic_light)
        self.pathfinder = AStarPathfinder(GRID_SIZE)
        self.data_collector = DataCollector()
        
        # Simulation state
        self.vehicles = []
        self.running = True
        self.paused = False
        self.sim_time = 0
        self.spawn_timer = 0
        self.log_timer = 0
        self.speed_multiplier = 1
        
    def spawn_vehicle(self):
        """Spawn new vehicle"""
        if len(self.vehicles) >= MAX_VEHICLES:
            return
        
        # Random type
        rand = random.random()
        if rand < 0.05:
            v_type = 'emergency'
        elif rand < 0.20:
            v_type = 'bus'
        elif rand < 0.35:
            v_type = 'truck'
        else:
            v_type = 'car'
        
        direction = random.choice(['north', 'south', 'east', 'west'])
        lane = random.randint(0, 1)
        
        vehicle = Vehicle(v_type, direction, lane)
        self.vehicles.append(vehicle)
    
    def update(self, dt):
        """Update simulation"""
        if self.paused:
            return
        
        dt *= self.speed_multiplier
        self.sim_time += dt
        
        # Spawn vehicles
        self.spawn_timer += dt
        if self.spawn_timer >= VEHICLE_SPAWN_RATE:
            self.spawn_timer = 0
            self.spawn_vehicle()
        
        # Agent perceives and decides
        perception = self.agent.perceive(self.vehicles)
        self.agent.decide(perception)
        
        # Update traffic light
        self.traffic_light.update(dt)
        
        # Update vehicles
        for vehicle in self.vehicles:
            can_go = self.traffic_light.can_go(vehicle.direction)
            
            # Check if near stop line
            center_x, center_y = WINDOW_WIDTH//2, WINDOW_HEIGHT//2
            distance_to_center = math.sqrt((vehicle.x - center_x)**2 + (vehicle.y - center_y)**2)
            
            if distance_to_center > 150:
                can_go = True
            
            vehicle.update(dt, can_go)
        
        # Remove crossed vehicles
        self.vehicles = [v for v in self.vehicles if not v.crossed]
        
        # Log data
        self.log_timer += dt
        if self.log_timer >= 1.0:
            self.log_timer = 0
            self.data_collector.log(self.sim_time, self.vehicles, 
                                   self.traffic_light, self.agent)
    
    def draw(self):
        """Draw everything"""
        self.screen.fill(BLACK)
        
        # Draw roads
        road_width = 200
        pygame.draw.rect(self.screen, GRAY, 
                        (WINDOW_WIDTH//2 - road_width//2, 0, road_width, WINDOW_HEIGHT))
        pygame.draw.rect(self.screen, GRAY,
                        (0, WINDOW_HEIGHT//2 - road_width//2, WINDOW_WIDTH, road_width))
        
        # Draw lane markings
        for i in range(0, WINDOW_HEIGHT, 40):
            pygame.draw.rect(self.screen, YELLOW,
                           (WINDOW_WIDTH//2 - 2, i, 4, 20))
        for i in range(0, WINDOW_WIDTH, 40):
            pygame.draw.rect(self.screen, YELLOW,
                           (i, WINDOW_HEIGHT//2 - 2, 20, 4))
        
        # Draw stop lines
        stop_dist = 150
        pygame.draw.rect(self.screen, WHITE,
                        (WINDOW_WIDTH//2 - road_width//2, WINDOW_HEIGHT//2 - stop_dist, road_width, 5))
        pygame.draw.rect(self.screen, WHITE,
                        (WINDOW_WIDTH//2 - road_width//2, WINDOW_HEIGHT//2 + stop_dist, road_width, 5))
        pygame.draw.rect(self.screen, WHITE,
                        (WINDOW_WIDTH//2 - stop_dist, WINDOW_HEIGHT//2 - road_width//2, 5, road_width))
        pygame.draw.rect(self.screen, WHITE,
                        (WINDOW_WIDTH//2 + stop_dist, WINDOW_HEIGHT//2 - road_width//2, 5, road_width))
        
        # Draw traffic lights
        self.traffic_light.draw(self.screen)
        
        # Draw vehicles
        for vehicle in self.vehicles:
            vehicle.draw(self.screen)
        
        # Draw dashboard
        self.draw_dashboard()
        
        # Draw title
        title = self.title_font.render("SMART TRAFFIC LIGHT CONTROLLER", True, WHITE)
        self.screen.blit(title, (20, 20))
        
        pygame.display.flip()
    
    def draw_dashboard(self):
        """Draw live metrics dashboard"""
        x, y = 1000, 80
        
        # Calculate metrics
        queues = {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        for v in self.vehicles:
            if not v.crossed:
                queues[v.direction] += 1
        
        total_wait = sum(v.wait_time for v in self.vehicles if not v.crossed)
        active_vehicles = len([v for v in self.vehicles if not v.crossed])
        avg_wait = total_wait / active_vehicles if active_vehicles > 0 else 0
        
        # Dashboard background
        pygame.draw.rect(self.screen, (50, 50, 50), (x - 10, y - 10, 380, 700), border_radius=10)

        
        # Title
        text = self.font.render("LIVE METRICS", True, ORANGE)
        self.screen.blit(text, (x, y))
        y += 40
        
        # Queue lengths
        text = self.font.render("Queue Lengths:", True, WHITE)
        self.screen.blit(text, (x, y))
        y += 30
        
        for direction in ['north', 'south', 'east', 'west']:
            count = queues[direction]
            bar_width = count * 20
            color = RED if count > 8 else ORANGE if count > 5 else GREEN
            
            text = self.font.render(f"{direction.capitalize()}: {count}", True, WHITE)
            self.screen.blit(text, (x, y))
            pygame.draw.rect(self.screen, color, (x + 120, y, min(bar_width, 200), 20))
            y += 30
        
        y += 10
        
        # Average wait time
        text = self.font.render(f"Avg Wait: {avg_wait:.1f}s", True, WHITE)
        self.screen.blit(text, (x, y))
        y += 30
        
        # Vehicles
        text = self.font.render(f"Active Vehicles: {active_vehicles}", True, WHITE)
        self.screen.blit(text, (x, y))
        y += 30
        
        crossed = Vehicle.vehicle_count - active_vehicles
        text = self.font.render(f"Crossed: {crossed}", True, WHITE)
        self.screen.blit(text, (x, y))
        y += 40
        
        # Current lights
        text = self.font.render("Traffic Lights:", True, WHITE)
        self.screen.blit(text, (x, y))
        y += 30
        
        ns_state = self.traffic_light.current_state['north-south']
        ns_color = GREEN if ns_state == 'green' else YELLOW if ns_state == 'yellow' else RED
        text = self.font.render(f"N-S: {ns_state.upper()}", True, ns_color)
        self.screen.blit(text, (x, y))
        y += 25
        
        ew_state = self.traffic_light.current_state['east-west']
        ew_color = GREEN if ew_state == 'green' else YELLOW if ew_state == 'yellow' else RED
        text = self.font.render(f"E-W: {ew_state.upper()}", True, ew_color)
        self.screen.blit(text, (x, y))
        y += 35
        
        # Time left
        time_left = self.traffic_light.phase_duration - self.traffic_light.timer
        text = self.font.render(f"Time Left: {time_left:.1f}s", True, WHITE)
        self.screen.blit(text, (x, y))
        y += 40
        
        # Agent decision
        text = self.font.render("Agent Decision:", True, ORANGE)
        self.screen.blit(text, (x, y))
        y += 30
        
        # Word wrap for decision
        decision_words = self.agent.last_decision.split()
        line = ""
        for word in decision_words:
            test_line = line + word + " "
            if len(test_line) > 30:
                text = self.font.render(line, True, WHITE)
                self.screen.blit(text, (x, y))
                y += 25
                line = word + " "
            else:
                line = test_line
        if line:
            text = self.font.render(line, True, WHITE)
            self.screen.blit(text, (x, y))
            y += 40
        
        # Controls
        text = self.font.render("Controls:", True, ORANGE)
        self.screen.blit(text, (x, y))
        y += 30
        
        controls = [
            "SPACE: Pause/Resume",
            "E: Spawn Emergency",
            "↑/↓: Speed",
            "R: Reset",
            "ESC: Exit"
        ]
        for control in controls:
            text = self.font.render(control, True, WHITE)
            self.screen.blit(text, (x, y))
            y += 25
        
        y += 10
        text = self.font.render(f"Speed: {self.speed_multiplier}x", True, YELLOW)
        self.screen.blit(text, (x, y))
        y += 25
        
        text = self.font.render(f"Time: {self.sim_time:.1f}s", True, WHITE)
        self.screen.blit(text, (x, y))
    
    def handle_events(self):
        """Handle user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_e:
                    self.spawn_emergency()
                elif event.key == pygame.K_UP:
                    self.speed_multiplier = min(5, self.speed_multiplier + 1)
                elif event.key == pygame.K_DOWN:
                    self.speed_multiplier = max(1, self.speed_multiplier - 1)
    
    def spawn_emergency(self):
        """Spawn emergency vehicle"""
        direction = random.choice(['north', 'south', 'east', 'west'])
        vehicle = Vehicle('emergency', direction, 0)
        self.vehicles.append(vehicle)
        print(f"Emergency vehicle spawned from {direction}")
    
    def reset(self):
        """Reset simulation"""
        self.vehicles = []
        self.sim_time = 0
        self.spawn_timer = 0
        Vehicle.vehicle_count = 0
        self.traffic_light = TrafficLight()
        self.agent = TrafficAgent(self.traffic_light)
        print("Simulation reset")
    
    def run(self):
        """Main simulation loop"""
        print("=" * 60)
        print("SMART TRAFFIC LIGHT CONTROLLER")
        print("=" * 60)
        print("\nStarting simulation...")
        print("Data will be logged to: data/traffic_data.csv")
        print("\nControls:")
        print("  SPACE: Pause/Resume")
        print("  E: Spawn emergency vehicle")
        print("  ↑/↓: Adjust speed")
        print("  R: Reset simulation")
        print("  ESC: Exit")
        print("\n" + "=" * 60)
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        print("\nSimulation ended.")
        print(f"Total vehicles processed: {Vehicle.vehicle_count}")
        print(f"Data saved to: data/traffic_data.csv")

# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    sim = TrafficSimulation()
    sim.run()