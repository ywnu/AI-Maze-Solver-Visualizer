# AI Maze Solver Visualizer

A visual tool that compares how different AI search algorithms perform in solving the same maze in real time.

## Overview
An interactive desktop application that generates random mazes and visually shows how four different AI search algorithms find their way from start to goal — step by step.

## Features
- Generates a new random maze each round
- Runs 4 algorithms: DFS, BFS, A* and Greedy
- Animates the exploration step by step
- Highlights the final path in a different color
- Displays live performance stats (cells explored, path length, time, efficiency)

## Algorithms Used

| Algorithm | Type | Shortest Path |
|-----------|------|--------------|
| DFS (Depth-First Search) | Stack | No |
| BFS (Breadth-First Search) | Queue | Yes |
| A* (A-Star Search) | Priority Queue | Yes |
| Greedy Best-First Search | Priority Queue | No |

## Results

| Algorithm | Cells Explored | Path Length | Efficiency |
|-----------|---------------|-------------|------------|
| DFS | 221 | 215 | 97% |
| Greedy | 247 | 215 | 87% |
| A* | 327 | 215 | 65% |
| BFS | 353 | 215 | 60% |

## How to Use

### Requirements
pip install pygame

### Run the Project
python "Ai Maze Solver Visualizer.py"

### Controls
| Key | Action |
|-----|--------|
| N | Next algorithm |
| R | New maze |
| SPACE | Auto/Pause |
| + | Faster |
| - | Slower |
| ESC | Exit |

## Team
- Deem Almaneea - [@ywnu](https://github.com/ywnu)
- Hanan Almutairi - [@lixr-7](https://github.com/lixr-7)
- Aseel Alotaibi
- Bayader Alotaibi
- Jumanah Alotaibi

## Course
Artificial Intelligence - CSC 2304 | Shaqra University
Instructor: Dr. Amirah Almutairi
Date: May 2026
