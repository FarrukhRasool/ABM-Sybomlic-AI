# model/city_model.py
#
# The Mesa Model for the "Waste in the City" simulation.
#
# Design decision: Mesa's MultiGrid is the single source of truth. Cell type
# is stored as a PropertyLayer attached to that grid; mobile agents (added in
# Steps 3+) will occupy the same grid. There is no separate city_map.
#
# CityGridBuilder produces a transient blueprint (a 2D list of cell-type
# strings). The model copies that blueprint into the grid's PropertyLayer
# once, at construction. The blueprint is not kept around afterwards.
#
# Scheduler wiring (RandomActivation) is deferred to sub-step 2.9.

from mesa import Model
from mesa.space import MultiGrid, PropertyLayer

from model.grid_builder import CityGridBuilder
from model.constants import GRID_WIDTH, GRID_HEIGHT, BUILDING

# Name of the PropertyLayer that holds each cell's semantic type.
CELL_TYPE_LAYER = "cell_type"


class CityModel(Model):
    def __init__(self, width=GRID_WIDTH, height=GRID_HEIGHT):
        super().__init__()

        # 1. Compute the semantic layout as a transient blueprint.
        blueprint = CityGridBuilder(width, height).build()

        # 2. Build a property layer holding the cell type per cell.
        #    dtype=object because cell types are strings, not numbers.
        cell_type_layer = PropertyLayer(
            CELL_TYPE_LAYER, width, height,
            default_value=BUILDING, dtype=object,
        )
        for x in range(width):
            for y in range(height):
                cell_type_layer.set_cell((x, y), blueprint[x][y])

        # 3. The MultiGrid owns both the property layer (cell type) and,
        #    later, the agents that move on it.
        self.grid = MultiGrid(
            width, height, torus=False,
            property_layers=cell_type_layer,
        )

    def get_cell_type(self, pos):
        x, y = pos
        return self.grid.properties[CELL_TYPE_LAYER].data[x][y]
