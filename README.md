# 🚦 Smart Traffic Light Controller

A comprehensive AI and Data Science project demonstrating intelligent traffic management using rule-based agents, A* pathfinding, and real-time statistical analysis.

## 📋 Project Overview

This project simulates a smart 4-way intersection with:
- **Intelligent Agent** for adaptive traffic light control
- **A* Pathfinding** algorithm for emergency vehicle routing
- **Real-time Data Collection** for traffic metrics
- **Statistical Analysis** with exploratory data analysis (EDA)
- **Interactive Visualization** using Pygame

---

## 📁 Simplified File Structure

```
smart-traffic-controller/
│
├── main.py              # Complete simulation (run this first!)
├── analyzer.py          # Statistical analysis & visualization
├── requirements.txt     # Python dependencies
├── README.md           # This file
│
└── data/               # Auto-created on first run
    ├── traffic_data.csv        # Collected data
    └── analysis/               # Analysis outputs
        ├── queue_over_time.png
        ├── wait_time_distribution.png
        ├── correlation_heatmap.png
        ├── avg_queue_by_direction.png
        ├── light_distribution.png
        ├── vehicle_throughput.png
        └── analysis_report.txt
```

**Only 3 files to manage!**

---

## 🎯 Learning Objectives Covered

### ✅ Unit 1: Introduction to AI
- Intelligent agent architecture (sensors, actuators, decision-making)
- Rule-based systems
- Real-world AI application
- Agent perception and action

### ✅ Unit 2: Problem Solving
- Problem formulation (emergency routing)
- State space representation (grid-based)
- **A* search algorithm** implementation
- Heuristic functions (Manhattan distance)
- Optimal pathfinding

### ✅ Unit 3: Introduction to Data Science
- Real-time data collection pipeline
- Data processing and storage (CSV)
- Data science workflow
- Role of data scientist

### ✅ Unit 4: Statistical Analysis
- Descriptive statistics (mean, median, std dev)
- Distribution analysis
- **Exploratory Data Analysis (EDA)**
- Correlation and covariance analysis
- Data visualization

### ✅ Unit 5: Statistical Applications
- Time series analysis (traffic patterns over time)
- Pattern identification
- Anomaly detection
- Performance metrics

**Coverage: ~85% of syllabus!**

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install pygame numpy pandas matplotlib seaborn scipy
```

Or use requirements file:
```bash
pip install -r requirements.txt
```

### 2. Run Simulation

```bash
python main.py
```

The simulation will:
- Open a Pygame window showing live traffic
- Display real-time metrics on dashboard
- Log data to `data/traffic_data.csv`
- Allow interactive control

### 3. Run Analysis

After running the simulation for a while (recommended: 2-5 minutes), press ESC to exit, then:

```bash
python analyzer.py
```

This will:
- Load collected data
- Perform statistical analysis
- Generate 6 visualization charts
- Create a comprehensive report

---

## 🎮 Controls

| Key | Action |
|-----|--------|
| **SPACE** | Pause/Resume simulation |
| **E** | Spawn emergency vehicle |
| **↑/↓** | Increase/Decrease speed (1x to 5x) |
| **R** | Reset simulation |
| **ESC** | Exit and save data |

---

## 🎨 Features

### 1. Traffic Environment
- 4-way intersection with 2 lanes per direction
- Multiple vehicle types: Car, Bus, Truck, Emergency
- Realistic queue formation at red lights
- Collision detection and avoidance

### 2. Intelligent Agent
**Rule-based decision system:**

```python
IF emergency_vehicle_detected:
    → IMMEDIATELY switch to green
    
ELIF queue_length > 10:
    → EXTEND green by 10 seconds
    
ELIF average_wait_time > 60s:
    → EXTEND green by 5 seconds
    
ELSE:
    → USE standard timing
```

### 3. A* Pathfinding
- Implements complete A* algorithm
- Manhattan distance heuristic
- Used for emergency vehicle routing
- Visualizes explored nodes (optional)

### 4. Data Collection
**Metrics collected every second:**
- Queue lengths (all 4 directions)
- Wait times (all 4 directions)
- Traffic light states
- Agent decisions
- Emergency activations
- Vehicle counts

### 5. Statistical Analysis
- **Descriptive Statistics**: Mean, median, std dev, variance
- **Distribution Analysis**: Skewness, kurtosis, normality tests
- **Correlation Analysis**: Heatmap of variable relationships
- **Pattern Identification**: Peak hours, congestion periods
- **Anomaly Detection**: Outlier detection using z-scores
- **Visualizations**: 6 comprehensive charts

---

## 📊 Output Examples

### Live Dashboard
```
┌──────────────────────────┐
│   LIVE METRICS           │
├──────────────────────────┤
│  Queue Lengths:          │
│  North:  ▮▮▮▮▮ (5)      │
│  South:  ▮▮▮ (3)        │
│  East:   ▮▮▮▮▮▮▮▮ (8)  │
│  West:   ▮▮ (2)         │
│                          │
│  Avg Wait: 15.3s         │
│  Active Vehicles: 24     │
│                          │
│  Traffic Lights:         │
│  N-S: GREEN              │
│  E-W: RED                │
│  Time Left: 12s          │
│                          │
│  Agent Decision:         │
│  "Extending green +5s    │
│   due to queue length"   │
└──────────────────────────┘
```

### Analysis Report Sample
```
KEY FINDINGS
────────────────────────────────
1. Average queue length: 4.23 vehicles
2. Maximum queue length: 12 vehicles
3. Average wait time: 18.45 seconds
4. Maximum wait time: 67.32 seconds
5. Total vehicles processed: 156
6. Emergency activations: 8

PERFORMANCE ASSESSMENT
────────────────────────────────
✓ EXCELLENT: Average wait time < 30s
✓ GOOD: Queue lengths manageable
```

---

## 🔬 Technical Implementation

### Vehicle Types
| Type | Speed | Priority | Size | Spawn Rate |
|------|-------|----------|------|------------|
| Car | 2.0 | Low | 20×30 | 60% |
| Bus | 1.2 | Medium | 25×45 | 20% |
| Truck | 1.0 | Low | 25×50 | 15% |
| Emergency | 3.5 | **HIGH** | 22×35 | 5% |

### Traffic Light State Machine
```
GREEN (30s) → YELLOW (5s) → RED (2s) → Next Phase
     ↑                                       ↓
     └───────────────────────────────────────┘
```

### A* Algorithm
```python
f(n) = g(n) + h(n)

where:
  g(n) = actual cost from start to n
  h(n) = Manhattan distance from n to goal
```

---

## 📈 Generated Visualizations

1. **Queue Over Time**: Line chart showing queue evolution
2. **Wait Time Distribution**: Histograms for each direction
3. **Correlation Heatmap**: Variable relationships
4. **Average Queue by Direction**: Bar chart comparison
5. **Light Distribution**: Pie charts of green/yellow/red time
6. **Vehicle Throughput**: Cumulative vehicles crossed

---

## 🧪 Extending the Project

### Easy Extensions
1. Add more vehicle types (motorcycles, bicycles)
2. Implement different agent strategies (compare performance)
3. Add weather conditions affecting traffic
4. Implement pedestrian crossings

### Advanced Extensions
1. Machine learning for adaptive timing
2. Multi-intersection network
3. Reinforcement learning agent
4. Real-time optimization algorithms

---

## 📚 Educational Value

### For Students
- **Understand AI agents** through concrete implementation
- **Learn A* algorithm** with visual demonstration
- **Practice data science** with real-world metrics
- **Apply statistics** to meaningful analysis
- **Build portfolio** with complete project

### For Instructors
- Covers 85%+ of typical AI + Data Science syllabus
- Combines theory with practical application
- Generates real data for analysis
- Demonstrates problem-solving approach
- Suitable for 2-3 week project timeline

---

## 🐛 Troubleshooting

**Issue**: Pygame window doesn't open
- **Solution**: Ensure pygame is installed: `pip install pygame`

**Issue**: No data file found when running analyzer
- **Solution**: Run `main.py` first to generate data

**Issue**: Simulation runs too slow
- **Solution**: Press ↑ to increase speed, or reduce MAX_VEHICLES in code

**Issue**: Charts not displaying
- **Solution**: Check matplotlib backend, ensure GUI support

---

## 📝 Assignment Submission Checklist

- [ ] `main.py` - Complete simulation code
- [ ] `analyzer.py` - Statistical analysis code
- [ ] `requirements.txt` - Dependencies list
- [ ] `data/traffic_data.csv` - Sample data (2-5 min simulation)
- [ ] `data/analysis/` - All 6 visualization charts
- [ ] `data/analysis/analysis_report.txt` - Analysis report
- [ ] `README.md` - Project documentation
- [ ] Screenshots of running simulation
- [ ] Report explaining AI concepts, algorithms, and findings

---

## 🎓 Project Complexity

- **Lines of Code**: ~800 (main.py) + ~400 (analyzer.py) = **~1200 total**
- **Time Required**: 1-2 weeks
- **Difficulty**: Medium
- **Prerequisites**: Basic Python, Pygame basics, pandas/matplotlib basics

---

## 📖 Key Concepts Demonstrated

### AI Concepts
- Intelligent agents (perception → reasoning → action)
- State-based systems
- Rule-based decision making
- Search algorithms (A*)
- Heuristic functions
- Problem formulation

### Data Science Concepts
- Data collection pipeline
- Time series data
- Descriptive statistics
- Distribution analysis
- Correlation analysis
- Data visualization
- Exploratory Data Analysis (EDA)
- Pattern recognition
- Anomaly detection

---

## 🏆 Learning Outcomes

After completing this project, you will be able to:

1. ✅ Design and implement an intelligent agent
2. ✅ Implement A* pathfinding algorithm
3. ✅ Collect and process real-time data
4. ✅ Perform comprehensive statistical analysis
5. ✅ Create meaningful data visualizations
6. ✅ Identify patterns and anomalies in data
7. ✅ Build interactive simulations with Pygame
8. ✅ Structure a complete AI + Data Science project

---

## 📞 Support

For questions or issues:
1. Check code comments for detailed explanations
2. Review README troubleshooting section
3. Examine generated analysis report for insights
4. Experiment with different configurations

---

## 🌟 Project Highlights

✨ **Complete**: All components working together
✨ **Educational**: Covers major syllabus topics
✨ **Practical**: Real-world application
✨ **Visual**: Interactive demonstration
✨ **Analyzable**: Generates real data and insights
✨ **Extendable**: Easy to add new features
✨ **Portfolio-Ready**: Professional presentation

---

## 📄 License

This project is created for educational purposes. Feel free to modify and extend for your learning needs.

---

**Happy Coding! 🚀**

*Built with Python, Pygame, NumPy, Pandas, Matplotlib, and Seaborn*