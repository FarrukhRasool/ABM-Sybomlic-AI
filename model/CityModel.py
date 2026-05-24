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

from agents.AgentFactory import AgentFactory
from agents.HumanAgent import HumanAgent
from agents.TouristAgent import TouristAgent

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
        self.factory = AgentFactory(self)
        # ── Dummy agent — keeps Mesa visualization happy ─────────────
        dummy = Agent(self)
        self.factory.spawn_humans(1)
        self.factory.spawn_tourists(1)
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
        x, y    = pos
        numeric = self.cell_types.data[x][y]  # ← direct array access
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
        # self.agents.shuffle_do("step")
        # self.factory.respawn_humans_if_needed(minimum=1)
        # self.factory.respawn_tourists_if_needed(minimum=1)
        humans = [a for a in self.agents if isinstance(a, HumanAgent)]
        def manhattan(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        humans = [a for a in self.agents if isinstance(a, HumanAgent)]

        for h in humans:
            # Check if human is near any bin
            for bin_pos, bin_obj in self.waste.bins.items():  # ← self.waste.bins
                if manhattan(h.pos, bin_pos) <= 1:
                    print(
                        f"🚶 Human at {h.pos} | "
                        f"Bin {bin_pos} [{bin_obj.level}/{bin_obj.capacity}] | "
                        f"Default units remaining: {h.waste_units}/5 | "
                        f"Extra waste generated: {h._waste_dropped}/{h._max_extra_waste} | "
                        f"Carrying extra waste: {h.carrying_extra_waste}"
                    )
            if h.carrying_extra_waste:
                print(f"🗑️  Holding extra litter: pos={h.pos} dest={h.destination}")

        # Print any bin that has waste in it
        for bin_pos, bin_obj in self.waste.bins.items():  # ← self.waste.bins
            if bin_obj.level > 0:
                print(f"📦 Bin {bin_pos} → level={bin_obj.level}/{bin_obj.capacity}")

        self.agents.shuffle_do("step")

        if len(humans) == 0:
            self.factory.spawn_humans(1)





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
    from agents.HumanAgent import HumanAgent
    

    if isinstance(agent, HumanAgent):
        return {
            "color":  "white",
            "marker": "o",
            "size":   250,
            "zorder": 3,
        }
    if isinstance(agent, TouristAgent):
        return {
            "color":  "black",
            "marker": "o",    # star shape — tourists stand out
            "size":   350,
            "zorder": 3,
        }
    return {
        "color":  "black",
        "marker": "o",
        "size":   1,
        "zorder": 1,
    }

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

    with solara.Column():                                    # ← wrap here
        solara.FigureMatplotlib(fig, dependencies=[])
    plt.close(fig)


# ================================================================== #
# Entry point                                                          #
# ================================================================== #

model_instance = CityModel()

space_component = make_mpl_space_component(
    agent_portrayal=agent_portrayal,
    propertylayer_portrayal=propertylayer_portrayal,
    post_process=make_figure_bigger,
)

@solara.component
def Page():
    with solara.Column():
        SolaraViz(
            model_instance,
            components=[space_component]
        )

page = Page
Page = Page

# Temporary test — remove after confirming
print("Bins found:", len(model_instance.waste.bins))
print("Containers found:", len(model_instance.waste.containers))
print("Stats:", model_instance.waste.get_stats())


print("(0,0) walkable?", model_instance.is_walkable((0, 0)))    # should be True (road)
print("(6,6) walkable?", model_instance.is_walkable((6, 6))) 