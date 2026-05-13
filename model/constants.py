# model/constants.py

# Cell types (semantic, not geometric)
ROAD = "road"
SIDEWALK = "sidewalk"
BUILDING = "building"
ATTRACTIVE = "attractive"
BIN = "bin"
CONTAINER = "container"
DISPOSAL = "disposal"

# Movement permissions (used later)
PEDESTRIAN_CELLS = {SIDEWALK, ATTRACTIVE}
SERVICE_CELLS = {ROAD, SIDEWALK, ATTRACTIVE}

# Grid size (can be tuned later)
GRID_WIDTH = 30
GRID_HEIGHT = 30
