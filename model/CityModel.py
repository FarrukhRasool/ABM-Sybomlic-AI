import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import solara

from mesa import Model, Agent
from mesa.space import MultiGrid, PropertyLayer
from mesa.visualization.components import PropertyLayerStyle, AgentPortrayalStyle
from mesa.visualization.components.matplotlib_components import make_mpl_space_component
from mesa.datacollection import DataCollector
from mesa.visualization import SolaraViz, make_plot_component
from matplotlib.colors import ListedColormap

from constants import *

from CityGridBuilder import CityGridBuilder
from waste.WasteManager import WasteManager

from agents.AgentFactory import AgentFactory
from agents.HumanAgent import HumanAgent
from agents.TouristAgent import TouristAgent
from agents.CleanerStreetAgent import CleanerStreetAgent
from agents.CleanerParkAgent import CleanerParkAgent
from agents.BinTransporterAgent import BinTransporterAgent
from agents.ContainerTransporterAgent import ContainerTransporterAgent
from agents.ModelCitizenAgent import ModelCitizenAgent


# ==================================================================
# Visualization configuration
# ==================================================================

CITY_CMAP = ListedColormap([
    "lightgrey",    # 0.0 road
    "saddlebrown",  # 1.0 building
    "gold",         # 2.0 attractive (park)
    "black",         # 3.0 door
    "limegreen",    # 4.0 bin
    "orange",       # 5.0 container
    "red",          # 6.0 disposal
    "crimson",      # 7.0 waste
 ])


# ================================================================== #
# Model                                                                
# ================================================================== #

class CityModel(Model):
    """
    The city simulation model.

    Main responsibilities:
        - Create and store the semantic city grid
        - Initialize the city layout through CityGridBuilder
        - Create and store the WasteManager service
        - Create agents through AgentFactory
        - Execute one simulation step for all agents
        - Collect global statistics for visualization
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

        # ── Agent creation ───────────────────────────────────────────
        dummy = Agent(self)
        # self.factory.spawn_humans(1)    
        # self.factory.spawn_tourists(1)
        # self.factory.spawn_one_cleaner_per_vertical_street()
        # self.factory.spawn_one_cleaner_per_horizontal_street()
        # self.factory.spawn_park_cleaners_five_sectors(capacity=CLEAN_AGENT_CAPACITY)
        # self.factory.spawn_bin_transporters_by_building_column(capacity=CLEAN_AGENT_CAPACITY)
        # self.factory.spawn_container_transporter_simple(capacity=CONTAINER_AGENT_CAPACITY)
        self.factory.spawn_model_citizens(count=1, capacity=1)
        self.grid.place_agent(dummy, (0, 0))

        # ── Ploting waste gestion ──────────────────────────────────────
        self.datacollector = DataCollector(
            model_reporters={
                "total_deposited": lambda m: m.waste.total_deposited,
                "total_cleaned": lambda m: m.waste.total_cleaned,
                "waste_on_streets": lambda m: int(m.waste.waste_grid.sum()),
                "full_bins": lambda m: sum(1 for b in m.waste.bins.values() if b.is_full),
                "full_containers": lambda m: sum(1 for c in m.waste.containers.values() if c.is_full),
            }
        )

        self.datacollector.collect(self)    


    # ==================================================================
    # Model setup helpers
    # ==================================================================

    def _build_city_grid(self) -> None:
        """
        Build city layout and write it to the PropertyLayer.
        """
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

    # ==================================================================
    # Grid helper methods used by agents
    # ==================================================================

    def get_cell_type(self, pos: tuple) -> str:
        """
        Return the string cell type at pos.
        """
        x, y    = pos
        numeric = self.cell_types.data[x][y]  # ← direct array access
        return {v: k for k, v in CELL_TYPE_MAP.items()}.get(numeric, "building")

    def is_walkable(self, pos: tuple) -> bool:
        """
        Return True if agents can walk on this cell.
        """
        return self.get_cell_type(pos) in (
            ROAD, ATTRACTIVE, DOOR, BIN, CONTAINER, DISPOSAL, WASTE
        )

    # ==================================================================
    # Simulation step
    # ==================================================================

    def step(self) -> None:
        """
        Execute one full simulation step.
        """
        self.agents.shuffle_do("step")
        # self.factory.respawn_tourists_if_needed(minimum=1)
        self.datacollector.collect(self)


# ================================================================== #
# Visualization helpers                                                 #
# ================================================================== #

def propertylayer_portrayal(layer):
    """
    Define how the semantic property layer is visualized.
    """
    if layer.name == "cell_types":
        return PropertyLayerStyle(
            colormap=CITY_CMAP,
            alpha=1.0,
            colorbar=False,
            vmin=0.0,
            vmax=7.0,
        )

def agent_portrayal(agent):
    """
    Define how each agent type is displayed on the map.
    """
    if isinstance(agent, HumanAgent):
        return {
            "color":  "white",
            "marker": "o",
            "size":   350,
            "zorder": 3,
        }
    if isinstance(agent, TouristAgent):
        return {
            "color":  "Navy",
            "marker": "o",    # star shape — tourists stand out
            "size":   350,
            "zorder": 3,
        }
    if isinstance(agent, CleanerStreetAgent):
        return{
            "color": "purple",
            "marker": "o",
            "size": 350,
            "zorder": 3,
        }
    if isinstance(agent, CleanerParkAgent):
        return {
            "color": "purple",
            "marker": "0",
            "size": 350,
            "zorder": 3,
        }
    if isinstance(agent, BinTransporterAgent):
        return {
            "color":  "blue",
            "marker": "o",
            "size":   350,
            "zorder": 3,
        }
    if isinstance(agent, ContainerTransporterAgent):
        return{
            "color": "deeppink",
            "marker": "o",
            "size": 350,
            "zorder": 3,
        }
    if isinstance(agent, ModelCitizenAgent):
        return {
            "color":  "red",
            "marker": "o",
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
    """
    Post-processing helper to enlarge the city-map figure.
    """
    ax.figure.set_size_inches(20, 20)

def make_city_map(model):
    """
    Build a standalone Matplotlib figure of the city semantic layer.
    """
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


# ==================================================================
# Visualization entry point
# ==================================================================

# Global model instance used by SolaraViz
model_instance = CityModel()

# Space/map component
space_component = make_mpl_space_component(
    agent_portrayal=agent_portrayal,
    propertylayer_portrayal=propertylayer_portrayal,
    post_process=make_figure_bigger,
)

# Standard Mesa plot component using DataCollector fields
waste_plot_component = make_plot_component(
    {
        "total_deposited": "red",
        "total_cleaned": "green",
        "waste_on_streets": "orange",
        "full_bins": "blue",
        "full_containers": "purple",
    }
)

@solara.component
def WasteStatsComponent(model):
    """
    Custom Matplotlib waste-statistics plot.

    Displays:
        - total waste produced
        - total waste cleaned
        - waste currently on streets
        - current summary values
    """
    df = model.datacollector.get_model_vars_dataframe().copy()
    print("GRAPH UPDATED")
    print(df.tail())

    fig, ax = plt.subplots(figsize=(10, 7))

    cols = ["total_deposited", "total_cleaned", "waste_on_streets"]
    labels = {
        "total_deposited": "Déchets produits",
        "total_cleaned": "Déchets ramassés",
        "waste_on_streets": "Déchets sur routes",
    }
    colors = {
        "total_deposited": "red",
        "total_cleaned": "green",
        "waste_on_streets": "orange",
    }
    markers = {
        "total_deposited": "o",
        "total_cleaned": "s",
        "waste_on_streets": "^",
    }
    linestyles = {
        "total_deposited": "--",
        "total_cleaned": "-",
        "waste_on_streets": ":",
    }

    if not df.empty:
        x = list(df.index)

        for col in cols:
            y = df[col].tolist()
            ax.plot(
                x,
                y,
                label=labels[col],
                color=colors[col],
                linewidth=2.5,
                marker=markers[col],
                markersize=5,
                linestyle=linestyles[col],
                alpha=0.9,
            )

            # highlight last point
            ax.scatter(x[-1], y[-1], color=colors[col], s=70, zorder=5)

        x_max = max(10, len(df) - 1)
        y_max = max(5, int(df[cols].max().max()))
    else:
        x_max = 10
        y_max = 5

    # origine en bas à gauche
    ax.set_xlim(0, x_max)
    ax.set_ylim(0, y_max + 1)

    ax.set_title("Gestion des déchets", fontsize=16)
    ax.set_xlabel("Temps", fontsize=12)
    ax.set_ylabel("Quantité", fontsize=12)
    ax.legend(fontsize=10, loc="upper left")
    ax.grid(True, alpha=0.3)

    ax.set_xticks(range(0, x_max + 1, max(1, x_max // 5)))
    ax.set_yticks(range(0, y_max + 2, max(1, (y_max + 1) // 5)))

    fig.tight_layout()

    # petit résumé en texte dans la figure
    if not df.empty:
        last = df.iloc[-1]
        summary = (
            f"Produit: {int(last['total_deposited'])}\n"
            f"Ramassé: {int(last['total_cleaned'])}\n"
            f"Routes: {int(last['waste_on_streets'])}\n"
            f"Bins pleines: {int(last['full_bins'])}\n"
            f"Containers pleins: {int(last['full_containers'])}"
        )
        ax.text(
            0.98, 0.02,
            summary,
            transform=ax.transAxes,
            fontsize=10,
            va="bottom",
            ha="right",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
        )

    solara.FigureMatplotlib(fig)
    plt.close(fig)


@solara.component
def Page():
    """
    Main Solara page for the simulation.

    Current live view:
        - city map
        - waste-management plot (Mesa built-in plotting component)
    """
    SolaraViz(
        model_instance,
        components=[space_component, waste_plot_component]
    )

# Solara page export
page = Page
Page = Page

# ------------------------------------------------------------
# Debug : Check the states of the simulation
# ------------------------------------------------------------
print("Bins found:", len(model_instance.waste.bins))
print("Containers found:", len(model_instance.waste.containers))
print("Stats:", model_instance.waste.get_stats())
print("(0,0) walkable?", model_instance.is_walkable((0, 0)))    # should be True (road)
print("(6,6) walkable?", model_instance.is_walkable((6, 6))) 