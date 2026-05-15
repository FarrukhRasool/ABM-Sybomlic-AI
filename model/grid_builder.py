# model/grid_builder.py
#
# Builds the semantic city map: a width x height matrix where each cell
# is a string from model.constants (ROAD, BUILDING, ATTRACTIVE, ...).
#
# Construction is incremental. The grid starts as solid BUILDING and each
# carve_* method overwrites a specific feature on top. This matches the
# project's step-by-step development contract (see .claude/WORKFLOW_RULES.md).

from model.constants import ATTRACTIVE, BUILDING, ROAD

# Spacing between parallel roads, in cells. With GRID_WIDTH=30 this yields
# roads at x = 0, 6, 12, 18, 24 (five vertical and five horizontal roads).
ROAD_SPACING = 6

# Anchors for attractive areas. Each anchor is the bottom-left corner of a
# 5x5 block (the interior of a road grid cell). With ROAD_SPACING=6 the
# interior of a block at road x..x+6 spans cells x+1..x+5 (inclusive).
ATTRACTIVE_ANCHORS = [
    (1, 1),     # South-West block
    (13, 13),   # Central block
    (19, 19),   # North-East block
]
ATTRACTIVE_SIZE = 5


class CityGridBuilder:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[BUILDING for _ in range(height)] for _ in range(width)]

    def build(self):
        self._carve_roads()
        self._carve_attractive_areas()
        # Sub-steps 2.6 – 2.8 will add bins, containers, and the disposal area.
        return self.grid

    def _carve_roads(self):
        # Vertical roads: full columns at every ROAD_SPACING-th x.
        for x in range(0, self.width, ROAD_SPACING):
            for y in range(self.height):
                self.grid[x][y] = ROAD

        # Horizontal roads: full rows at every ROAD_SPACING-th y.
        for y in range(0, self.height, ROAD_SPACING):
            for x in range(self.width):
                self.grid[x][y] = ROAD

    def _carve_attractive_areas(self):
        # Each anchor (ax, ay) becomes the bottom-left of an ATTRACTIVE_SIZE
        # square. Cells inside the square overwrite their previous type
        # (typically BUILDING). Walkable plazas, conceptually.
        for ax, ay in ATTRACTIVE_ANCHORS:
            for x in range(ax, ax + ATTRACTIVE_SIZE):
                for y in range(ay, ay + ATTRACTIVE_SIZE):
                    self.grid[x][y] = ATTRACTIVE
