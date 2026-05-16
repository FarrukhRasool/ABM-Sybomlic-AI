import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import solara

from mesa import Model, Agent
from mesa.space import MultiGrid, PropertyLayer
from mesa.visualization import SolaraViz
from mesa.visualization.components import PropertyLayerStyle, AgentPortrayalStyle
from mesa.visualization.components.matplotlib_components import make_mpl_space_component
from matplotlib.colors import ListedColormap

from constants import *
from CityGridBuilder import CityGridBuilder
from waste.WasteManager import WasteManager


# ================================================================== #
# Visualization config                                                 #
# ================================================================== #

CITY_CMAP = ListedColormap([
    "lightgrey",    # 0.0 road
    "saddlebrown",  # 1.0 building
    "gold",         # 2.0 attractive (park)
    "blue",         # 3.0 door
    "limegreen",    # 4.0 bin
    "orange",       # 5.0 container
    "red",          # 6.0 disposal
    "crimson",      # 7.0 waste
])


# ================================================================== #
# Model                                                                #
# ================================================================== #

class CityModel(Model):
    """
    The city simulation model.

    Responsibilities:
        - Own the grid and property layer
        - Initialize all infrastructure via CityGridBuilder
        - Own the WasteManager service
        - Orchestrate agent steps each tick
    """

    def __init__(self, **kwargs):
        super().__init__()

        # ── Grid and property layer ──────────────────────────────────
        self.cell_types = PropertyLayer(
            "cell_types", GRID_WIDTH, GRID_HEIGHT,
            default_value=CELL_TYPE_MAP["building"],
            dtype=float
        )
        self.grid = MultiGrid(
            GRID_WIDTH, GRID_HEIGHT,
            torus=False,
            property_layers=self.cell_types
        )

        # ── Build city layout ────────────────────────────────────────
        self._build_city_grid()

        # ── Waste management service ─────────────────────────────────
        WasteManager.reset()             # ensure clean singleton on reset
        self.waste = WasteManager(self)

        # ── Dummy agent — keeps Mesa visualization happy ─────────────
        dummy = Agent(self)
        self.grid.place_agent(dummy, (0, 0))

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def _build_city_grid(self) -> None:
        """Build city layout and write it to the PropertyLayer."""
        builder   = CityGridBuilder(GRID_WIDTH, GRID_HEIGHT)
        city_grid = builder.build()

        # Vectorized numpy assignment — fast on 500x500
        data = np.array(
            [[CELL_TYPE_MAP.get(city_grid[x][y], CELL_TYPE_MAP["building"])
              for y in range(GRID_HEIGHT)]
             for x in range(GRID_WIDTH)],
            dtype=float
        )
        self.cell_types.data[:] = data

    # ------------------------------------------------------------------ #
    # Helpers — used by agents                                            #
    # ------------------------------------------------------------------ #

    def get_cell_type(self, pos: tuple) -> str:
        """Return the string cell type at pos."""
        numeric = self.cell_types.get_cell(pos)
        return {v: k for k, v in CELL_TYPE_MAP.items()}.get(numeric, "building")

    def is_walkable(self, pos: tuple) -> bool:
        """Return True if agents can walk on this cell."""
        return self.get_cell_type(pos) in (
            ROAD, ATTRACTIVE, DOOR, BIN, CONTAINER, DISPOSAL
        )

    # ------------------------------------------------------------------ #
    # Simulation step                                                      #
    # ------------------------------------------------------------------ #

    def step(self) -> None:
        """Advance simulation by one tick."""
        self.agents.shuffle_do("step")


# ================================================================== #
# Visualization                                                        #
# ================================================================== #

def propertylayer_portrayal(layer):
    if layer.name == "cell_types":
        return PropertyLayerStyle(
            colormap=CITY_CMAP,
            alpha=1.0,
            colorbar=False,
            vmin=0.0,
            vmax=7.0,
        )

def agent_portrayal(agent):
    return AgentPortrayalStyle(color="black", marker="o", size=1, alpha=0)

def make_figure_bigger(ax):
    ax.figure.set_size_inches(16, 16)

def make_city_map(model):
    fig, ax = plt.subplots(figsize=(20, 20))
    data    = model.cell_types.data.T
    ax.imshow(
        data,
        origin="lower",
        cmap=CITY_CMAP,
        vmin=0.0,
        vmax=7.0,
        interpolation="nearest",
        aspect="equal"
    )
    ax.set_title("City Map", fontsize=16)
    solara.FigureMatplotlib(fig, dependencies=[])
    plt.close(fig)


# ================================================================== #
# Entry point                                                          #
# ================================================================== #

model_instance = CityModel()

page = SolaraViz(
    model_instance,
    components=[make_city_map]
)

Page = page