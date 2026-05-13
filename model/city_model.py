# model/city_model.py

from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation

from model.grid_builder import CityGridBuilder
from model.constants import *

class CityModel(Model):
    def __init__(self, width=GRID_WIDTH, height=GRID_HEIGHT):
        super().__init__()

        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)

        # Semantic city map (environment metadata)
        self.city_map = CityGridBuilder(width, height).build()

    def step(self):
        self.schedule.step()
    

    def get_cell_type(self, pos):
        x, y = pos
        return self.city_map[x][y]
