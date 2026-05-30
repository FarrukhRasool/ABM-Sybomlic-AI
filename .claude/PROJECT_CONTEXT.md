# Project Context
## Waste in the City – Agent-Based Model

### 🏙️ Environment
A grid-based city consisting of semantically distinct cell types, designed to model pedestrian and service movement without unnecessary geometric complexity:

- Perpendicular roads arranged grid
- Buildings as non-walkable blocks that serve as start and end points for agents
- Attractive areas that influence agent movement and waste generation:
  - Central
  - North-East
  - South-West
- Infrastructure elements:
  - Bins placed at road intersections (low waste capacity)
  - Containers placed in the North-West and South-East of the city (high waste capacity)
  - A disposal area that permanently removes waste from the system

---

### 👥 Agents

#### Local Humans
- Follow fixed A → B walking routes (one predefined pattern per human)
- Start and end their movement inside buildings (agents disappear at route completion)
- Generate small amounts of waste during their walk
- Prefer dropping waste into bins when available
- If a bin is full, wait briefly; on overflow, drop waste in a nearby cell
- Medium walking speed
- Soft anti-collision behavior (wait or reroute locally)
- Move primarily on sidewalk cells

---

#### Tourists
- Perform random walks with fixed start and end buildings
- Prefer moving through attractive areas
- Stay longer in attractive areas and generate increased waste there
- Generate more waste than local humans
- Drop waste both into bins and directly onto sidewalks or roads
- Slowest walking speed among agents
- Soft anti-collision behavior
- Prefer less crowded pedestrian cells when possible

---

#### Cleaning Services
- Multiple cleaning agents, each responsible for a designated city area
- Follow regular patrol patterns within their assigned regions
- Detect and collect waste from sidewalks, roads, and attractive areas
- Have limited carrying capacity
- When capacity is reached, navigate to the disposal area
- Use A* pathfinding for efficient navigation

---

#### Transporters
- Multiple transporter agents assigned to specific city areas
- Follow regular routes along road cells
- Empty bins and containers when encountered
- Have limited carrying capacity
- Navigate to the disposal area when full
- Use A* pathfinding for route planning

---

### ♻️ Waste Model
- Waste is represented as **cell-level state**, not as an agent
- Waste flow follows this process:
  - Humans and tourists generate waste
  - Waste is deposited into bins or containers when possible
  - Transporters move waste from bins and containers to the disposal area
  - Overflow waste spills into nearby cells
  - Cleaning agents collect environmental waste and deliver it to the disposal area

---

### 🎯 Research Goal
To study **emergent city-level waste distribution** resulting from:
- Agent movement patterns
- Bin and container placement
- Cleaning strategies
- Tourist density
- Transporter frequency

---

### ⚠️ Key Principle
The focus of this project is on **emergent behavior at the system level**, not on optimizing the performance of any single agent.