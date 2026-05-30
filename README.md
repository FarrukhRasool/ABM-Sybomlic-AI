# Waste in the City — Agent-Based Model

An agent-based simulation of pedestrian movement, waste generation, and cleaning
services in a grid-based city. Built with Python and the
[Mesa](https://mesa.readthedocs.io/) ABM framework, the model studies how
city-level waste distribution emerges from the interaction of residents,
tourists, bin and container infrastructure, and a fleet of cleaning and
transport agents.

This project is part of the *Symbolic AI* course (3rd semester, MAI). The
implementation follows the component, use-case, and sequence diagrams stored in
`Diagrams/`.

---

## Overview

The simulated city consists of perpendicular roads, building blocks, a
cross-shaped park (attractive area), bins at the edges of building blocks,
larger containers at road intersections, and disposal zones on the city's east
and west borders.

The waste lifecycle is as follows:

1. Humans and tourists generate waste as they move.
2. Waste is preferably deposited into nearby bins, or otherwise dropped on the
   ground.
3. Bin transporters periodically empty bins into containers.
4. Container transporters periodically empty containers at the disposal area.
5. Street and park cleaners pick up waste left on roads and in the park, and
   also unload at the disposal area.

The focus is on emergent, system-level behavior rather than on the performance
of any single agent.

---

## Agents

| Agent | Role |
| --- | --- |
| `HumanAgent` | Local resident moving door to door; drops waste into bins when nearby, otherwise on the road. |
| `TouristAgent` | Visitor with a park-biased random walk and a higher waste-generation rate. |
| `ModelCitizenAgent` | Prosocial citizen that picks up roadside waste and carries it to the nearest available bin. |
| `CleanerStreetAgent` | Patrols a fixed street route, collects waste, and offloads at the disposal area when full. |
| `CleanerParkAgent` | Same logic as the street cleaner, restricted to the park sector. |
| `BinTransporterAgent` | Empties bins along a building-column route and transfers their content to containers. |
| `ContainerTransporterAgent` | Empties containers and routes the waste to the disposal area. |

All agents share a common `perceive → decide → act` cognitive loop defined in
`BaseAgent`.

---

## Architecture

```
model/
├── CityModel.py          # Mesa model, simulation loop, Solara visualization
├── CityGridBuilder.py    # Generates the semantic city map
├── constants.py          # Cell-type vocabulary, grid dimensions, capacities
├── agents/               # All agent classes and the AgentFactory
├── planning/             # SectorPlanner and PatrolPlanner (patrol-route generation)
└── waste/                # Bin, Container, and WasteManager
```

Key design points:

- The Mesa `MultiGrid` is the single source of truth. Cell types are stored in
  a numeric `PropertyLayer` and rendered via a categorical colormap.
- `WasteManager` is a singleton that owns the waste grid, bins, and containers,
  and notifies observers on events such as `bin_full`, `container_full`,
  `waste_appeared`, and `area_clean`.
- `SectorPlanner` discovers spatial groupings (streets, park sectors, building
  columns) from the live grid. `PatrolPlanner` turns those groupings into
  ordered patrol routes consumed by cleaners and transporters at spawn time.

---

## Requirements

- Python 3.11
- Mesa 3.x
- Solara
- NumPy
- Matplotlib

---

## Installation

```bash
python -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

---

## Running the simulation

Launch the Solara dashboard from the project root:

```bash
solara run model/CityModel.py
```

A browser tab opens with the live city map and the waste-statistics plot.

---

## Configuration

Static parameters (grid dimensions, block sizes, bin and container capacities,
agent capacities) are defined in `model/constants.py`. Per-agent behavior
parameters (waste probability, visit duration, park attraction) live as class
constants on each agent.

A `CityModel` instance can also be parametrized programmatically:

```python
from model.CityModel import CityModel

model = CityModel(
    num_humans=5,
    num_tourists=8,
    num_model_citizens=2,
    street_cleaner_capacity=3,
    park_cleaner_capacity=2,
    bin_transporter_capacity=5,
    container_transporter_capacity=10,
    model_citizen_capacity=4,
)
```

---

## Troubleshooting

If the default Solara port is already in use, free it and restart on a
different port.

**Windows**

```bash
netstat -ano | findstr :8766
taskkill /PID <PID> /F
solara run model/CityModel.py --port 8767
```

**macOS / Linux**

```bash
lsof -i :8766
kill -9 <PID>
solara run model/CityModel.py --port 8767
```