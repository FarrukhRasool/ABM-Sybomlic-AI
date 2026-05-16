# model/CityGridBuilder.py

from constants import *
import random

ROAD_WIDTH = 2
BLOCK_SIZE = 12
NUM_BLOCKS = 5
MARGIN     = 4

# How many bins to place randomly near each building block
BINS_PER_BLOCK = 2

class CityGridBuilder:
    def __init__(self, width, height, seed=42):
        self.width  = width
        self.height = height
        self.rng    = random.Random(seed)  # seeded for reproducibility
        self.grid   = [[ROAD for _ in range(height)] for _ in range(width)]
        self.mid    = NUM_BLOCKS // 2

        cursor = MARGIN
        self.road_starts = []
        for i in range(NUM_BLOCKS + 1):
            self.road_starts.append(cursor)
            cursor += ROAD_WIDTH
            if i < NUM_BLOCKS:
                cursor += BLOCK_SIZE

        self.blocks = [
            (self.road_starts[i] + ROAD_WIDTH, self.road_starts[i + 1])
            for i in range(NUM_BLOCKS)
        ]

    # ------------------------------------------------------------------ #
    # Public                                                               #
    # ------------------------------------------------------------------ #

    def build(self):
        self._carve_buildings()
        self._carve_park()
        self._carve_doors()
        self._carve_bins()
        self._carve_containers()
        self._carve_disposal()
        return self.grid

    # ------------------------------------------------------------------ #
    # Private                                                              #
    # ------------------------------------------------------------------ #

    def _is_park_block(self, col, row):
        mid = self.mid
        return (col == mid and abs(row - mid) <= 1) or \
               (row == mid and abs(col - mid) <= 1)

    def _carve_buildings(self):
        for (bx_start, bx_end) in self.blocks:
            for (by_start, by_end) in self.blocks:
                for x in range(bx_start, bx_end):
                    for y in range(by_start, by_end):
                        self.grid[x][y] = BUILDING

    def _carve_park(self):
        mid = self.mid
        cx_start, cx_end = self.blocks[mid]
        cy_start, cy_end = self.blocks[mid]

        v_y_start = self.blocks[mid - 1][0]
        v_y_end   = self.blocks[mid + 1][1]
        h_x_start = self.blocks[mid - 1][0]
        h_x_end   = self.blocks[mid + 1][1]

        for x in range(cx_start, cx_end):
            for y in range(v_y_start, v_y_end):
                self.grid[x][y] = ATTRACTIVE

        for x in range(h_x_start, h_x_end):
            for y in range(cy_start, cy_end):
                self.grid[x][y] = ATTRACTIVE

    def _carve_doors(self):
        for col, (bx_start, bx_end) in enumerate(self.blocks):
            for row, (by_start, by_end) in enumerate(self.blocks):
                if self._is_park_block(col, row):
                    continue
                self.grid[bx_start    ][by_end - 1] = DOOR
                self.grid[bx_end - 1  ][by_end - 1] = DOOR

    def _carve_bins(self):
        """Place BINS_PER_BLOCK bins randomly on road cells adjacent to each building block.
        Rules:
        - No two bins on the same side of a block
        - Bins cannot be placed adjacent to door cells
        """
        for col, (bx_start, bx_end) in enumerate(self.blocks):
            for row, (by_start, by_end) in enumerate(self.blocks):
                if self._is_park_block(col, row):
                    continue

                # Collect candidates per side separately
                sides = {
                    "bottom": [],
                    "top":    [],
                    "left":   [],
                    "right":  [],
                }

                # Bottom road strip (y = by_start - 1)
                if by_start - 1 >= 0:
                    for x in range(bx_start, bx_end):
                        pos = (x, by_start - 1)
                        if self.grid[x][by_start - 1] == ROAD and \
                        not self._is_near_door(x, by_start - 1):
                            sides["bottom"].append(pos)

                # Top road strip (y = by_end)
                if by_end < self.height:
                    for x in range(bx_start, bx_end):
                        pos = (x, by_end)
                        if self.grid[x][by_end] == ROAD and \
                        not self._is_near_door(x, by_end):
                            sides["top"].append(pos)

                # Left road strip (x = bx_start - 1)
                if bx_start - 1 >= 0:
                    for y in range(by_start, by_end):
                        pos = (bx_start - 1, y)
                        if self.grid[bx_start - 1][y] == ROAD and \
                        not self._is_near_door(bx_start - 1, y):
                            sides["left"].append(pos)

                # Right road strip (x = bx_end)
                if bx_end < self.width:
                    for y in range(by_start, by_end):
                        pos = (bx_end, y)
                        if self.grid[bx_end][y] == ROAD and \
                        not self._is_near_door(bx_end, y):
                            sides["right"].append(pos)

                # Pick one bin per side, from different sides only
                available_sides = [s for s in sides.values() if len(s) > 0]
                self.rng.shuffle(available_sides)  # randomize side order

                placed = 0
                for side_candidates in available_sides:
                    if placed >= BINS_PER_BLOCK:
                        break
                    chosen = self.rng.choice(side_candidates)
                    self.grid[chosen[0]][chosen[1]] = BIN
                    placed += 1

    def _is_near_door(self, x, y):
        """Return True if (x, y) is adjacent to a DOOR cell."""
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[nx][ny] == DOOR:
                        return True
        return False

    def _carve_containers(self):
        """Place containers at every other road intersection."""
        # Intersections are where road_starts[i] crosses road_starts[j]
        # Use every other road_start in each axis to avoid overcrowding
        for i, rx in enumerate(self.road_starts):
            for j, ry in enumerate(self.road_starts):
                if i % 2 == 0 and j % 2 == 0:  # every other intersection
                    # Place container at center of intersection (rx+1, ry+1)
                    cx = rx + ROAD_WIDTH // 2
                    cy = ry + ROAD_WIDTH // 2
                    if 0 <= cx < self.width and 0 <= cy < self.height:
                        if self.grid[cx][cy] == ROAD:
                            self.grid[cx][cy] = CONTAINER

    def _carve_disposal(self):
        """Place disposal areas on left and right sides at city center height."""
        mid_y     = self.height // 2
        half_size = 4  # cells above and below center

        for dy in range(-half_size, half_size + 1):
            # Left side
            self.grid[1][mid_y + dy] = DISPOSAL
            # Right side
            self.grid[self.width - 2][mid_y + dy] = DISPOSAL