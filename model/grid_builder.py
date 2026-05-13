# model/grid_builder.py

from model.constants import *

class CityGridBuilder:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(height)] for _ in range(width)]

    def build(self):
        self._init_empty()
        self._build_roads()
        self._build_sidewalks()
        self._build_buildings()
        self._build_attractive_areas()
        self._place_bins_and_containers()
        self._place_disposal_area()
        return self.grid

    def _init_empty(self):
        for x in range(self.width):
            for y in range(self.height):
                self.grid[x][y] = SIDEWALK

    def _build_roads(self):
        for x in range(0, self.width, 6):
            for y in range(self.height):
                self.grid[x][y] = ROAD

        for y in range(0, self.height, 6):
            for x in range(self.width):
                self.grid[x][y] = ROAD

    def _build_sidewalks(self):
        # sidewalks already default; semantic separation only
        pass

    def _build_buildings(self):
        for x in range(2, self.width, 6):
            for y in range(2, self.height, 6):
                self.grid[x][y] = BUILDING

    def _build_attractive_areas(self):
        center = (self.width // 2, self.height // 2)
        self.grid[center[0]][center[1]] = ATTRACTIVE
        self.grid[self.width - 3][self.height - 3] = ATTRACTIVE
        self.grid[2][2] = ATTRACTIVE

    def _place_bins_and_containers(self):
        # bins at road intersections
        for x in range(0, self.width, 6):
            for y in range(0, self.height, 6):
                self.grid[x][y] = BIN

        # containers
        self.grid[1][self.height - 2] = CONTAINER
        self.grid[self.width - 2][1] = CONTAINER

    def _place_disposal_area(self):
        self.grid[self.width - 1][self.height // 2] = DISPOSAL