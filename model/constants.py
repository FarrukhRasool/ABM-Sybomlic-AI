# model/constants.py

# Cell types (semantic, not geometric).
# Roads are the only walkable surface — there are no sidewalks.
ROAD       = "road"
BUILDING   = "building"
ATTRACTIVE = "attractive"
DOOR       = "door"
BIN        = "bin"
CONTAINER  = "container"
DISPOSAL   = "disposal"
WASTE      = "waste"


CELL_TYPE_MAP = {
    "road":       0.0,
    "building":   1.0,
    "attractive": 2.0,
    "door":       3.0,
    "bin":        4.0,
    "container":  5.0,
    "disposal":   6.0,
    "waste":      7.0,
}


BIN_CAPACITY       = 0   # max waste units a bin can hold
CONTAINER_CAPACITY = 50   # max waste units a container can hold


# Grid size (can be tuned later)
GRID_WIDTH = 80
GRID_HEIGHT = 80

ROAD_WIDTH = 2
BLOCK_SIZE = 12
NUM_BLOCKS = 5
MARGIN     = 4

CLEAN_AGENT_CAPACITY = 1  # max waste units a cleaner can carry
CONTAINER_AGENT_CAPACITY = 10  # max waste units a container transporter can carry