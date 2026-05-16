# model/constants.py

# Cell types (semantic, not geometric).
# Roads are the only walkable surface — there are no sidewalks.
ROAD = "road"
BUILDING = "building"
ATTRACTIVE = "attractive"
BIN = "bin"
CONTAINER = "container"
DISPOSAL = "disposal"
DOOR = "door"
# Grid size (can be tuned later)
GRID_WIDTH = 80
GRID_HEIGHT = 80
ROAD_WIDTH = 2
BLOCK_SIZE = 12
NUM_BLOCKS = 5
MARGIN     = 4