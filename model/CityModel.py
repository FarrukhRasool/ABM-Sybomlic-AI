
from mesa import Model, Agent
from mesa.space import MultiGrid, PropertyLayer
from mesa.visualization import SolaraViz
from mesa.visualization.components import PropertyLayerStyle, AgentPortrayalStyle
from mesa.visualization.components.matplotlib_components import make_mpl_space_component
from constants import *
from CityGridBuilder import CityGridBuilder
from matplotlib.colors import ListedColormap

CELL_TYPE_MAP = {
    "road":       0.0,
    "building":   1.0,
    "attractive": 2.0,
    "door":       3.0,
    "bin":        4.0,
    "container":  5.0,
    "disposal":   6.0,
}

CITY_CMAP = ListedColormap([
    "lightgrey",    # 0.0 road
    "saddlebrown",  # 1.0 building
    "gold",         # 2.0 attractive (park)
    "blue",         # 3.0 door
    "limegreen",    # 4.0 bin
    "orange",       # 5.0 container
    "red",          # 6.0 disposal
])

class CityModel(Model):
    def __init__(self, **kwargs):
        super().__init__()

        self.cell_types = PropertyLayer(
            "cell_types", GRID_WIDTH, GRID_HEIGHT,
            default_value=1.0,
            dtype=float
        )
        self.grid = MultiGrid(
            GRID_WIDTH, GRID_HEIGHT,
            torus=False,
            property_layers=self.cell_types
        )
        self._build_city_grid()

        # Invisible dummy agent so Mesa doesn't crash on empty grid
        dummy = Agent(self)
        self.grid.place_agent(dummy, (0, 0))

    def _build_city_grid(self):
        builder = CityGridBuilder(GRID_WIDTH, GRID_HEIGHT)
        city_grid = builder.build()
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                self.cell_types.set_cell((x, y), CELL_TYPE_MAP.get(city_grid[x][y], 1.0))

    def get_cell_type(self, pos):
        numeric = self.cell_types.get_cell(pos)
        return {v: k for k, v in CELL_TYPE_MAP.items()}.get(numeric, "building")


def propertylayer_portrayal(layer):
    if layer.name == "cell_types":
        return PropertyLayerStyle(
            colormap=CITY_CMAP,
            alpha=1.0,
            colorbar=False,
            vmin=0.0,
            vmax=6.0,
        )

def agent_portrayal(agent):
    # Dummy agent is invisible — size 0, fully transparent
    return AgentPortrayalStyle(color="black", marker="o", size=1, alpha=0)


model_instance = CityModel()

space_component = make_mpl_space_component(
    agent_portrayal=agent_portrayal,
    propertylayer_portrayal=propertylayer_portrayal,
)

page = SolaraViz(
    model_instance,
    components=[space_component]
)