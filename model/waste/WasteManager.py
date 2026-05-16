# waste/WasteManager.py

import numpy as np
from abc import ABC, abstractmethod
from constants import *
from waste.Bin import Bin
from waste.Container import Container


class WasteObserver(ABC):
    @abstractmethod
    def on_event(self, event: str, **kwargs) -> None:
        """
        Events:
            "bin_full"       → pos=(x,y)
            "container_full" → pos=(x,y)
            "waste_appeared" → pos=(x,y)
            "area_clean"     → pos=(x,y)
        """


class WasteManager:
    """
    Single source of truth for waste state in the city.
    Responsibilities:
        1. Store waste data (_waste_grid, bins, containers)
        2. Mutate state when agents interact with it
        3. Notify observers on key events
        4. Provide stats for the dashboard

    Does NOT:
        - Search for nearest waste (CleaningAgent's job)
        - Decide where to go (agent's job)
        - Know about agent strategies (Strategy Pattern's job)
    """

    _instance = None

    # ------------------------------------------------------------------ #
    # Singleton                                                            #
    # ------------------------------------------------------------------ #

    def __new__(cls, model):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model):
        if self._initialized:
            return
        self._initialized = True

        self.model  = model
        self.width  = model.grid.width
        self.height = model.grid.height

        self._waste_grid          = np.zeros((self.width, self.height), dtype=int)
        self._original_cell_types = model.cell_types.data.copy()
        self._bins:       dict[tuple, Bin]       = {}
        self._containers: dict[tuple, Container] = {}
        self._observers:  list[WasteObserver]    = []

        # Stats — only WasteManager tracks these
        self.total_deposited = 0
        self.total_cleaned   = 0
        self.total_trips     = 0

        self._init_infrastructure()

    @classmethod
    def reset(cls):
        """Call this when Mesa resets the model."""
        cls._instance = None

    # ------------------------------------------------------------------ #
    # Observer                                                             #
    # ------------------------------------------------------------------ #

    def register(self, observer: WasteObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unregister(self, observer: WasteObserver) -> None:
        self._observers = [o for o in self._observers if o is not observer]

    def _notify(self, event: str, **kwargs) -> None:
        for observer in self._observers:
            observer.on_event(event, **kwargs)

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def _init_infrastructure(self) -> None:
        for x in range(self.width):
            for y in range(self.height):
                val = self._original_cell_types[x][y]
                if val == CELL_TYPE_MAP["bin"]:
                    self._bins[(x, y)] = Bin(pos=(x, y))
                elif val == CELL_TYPE_MAP["container"]:
                    self._containers[(x, y)] = Container(pos=(x, y))

    # ------------------------------------------------------------------ #
    # State mutations — called by agents                                  #
    # ------------------------------------------------------------------ #

    def add_waste(self, pos: tuple, amount: int = 1) -> None:
        x, y = pos
        if self._original_cell_types[x][y] not in (
            CELL_TYPE_MAP["road"], CELL_TYPE_MAP["attractive"]
        ):
            return
        self._waste_grid[x][y] += amount
        self.total_deposited   += amount
        self.model.cell_types.set_cell(pos, CELL_TYPE_MAP["waste"])
        self._notify("waste_appeared", pos=pos)

    def clean_waste(self, pos: tuple, amount: int = 1) -> int:
        x, y    = pos
        cleaned = min(self._waste_grid[x][y], amount)
        self._waste_grid[x][y] -= cleaned
        self.total_cleaned     += cleaned
        if self._waste_grid[x][y] == 0:
            self.model.cell_types.set_cell(pos, self._original_cell_types[x][y])
            self._notify("area_clean", pos=pos)
        return cleaned

    def deposit_to_bin(self, pos: tuple, amount: int) -> int:
        if pos not in self._bins:
            return amount
        overflow = self._bins[pos].deposit(amount)
        if self._bins[pos].is_full:
            self._notify("bin_full", pos=pos)
        return overflow

    def empty_bin(self, pos: tuple) -> int:
        return self._bins[pos].empty() if pos in self._bins else 0

    def deposit_to_container(self, pos: tuple, amount: int) -> int:
        if pos not in self._containers:
            return amount
        overflow = self._containers[pos].deposit(amount)
        if self._containers[pos].is_full:
            self._notify("container_full", pos=pos)
        return overflow

    def empty_container(self, pos: tuple) -> int:
        return self._containers[pos].empty() if pos in self._containers else 0

    # ------------------------------------------------------------------ #
    # Read-only data access — agents query these for decisions            #
    # ------------------------------------------------------------------ #

    @property
    def waste_grid(self) -> np.ndarray:
        """Read-only view of waste grid for agent perception."""
        return self._waste_grid

    @property
    def bins(self) -> dict:
        """Read-only access to bin objects."""
        return self._bins

    @property
    def containers(self) -> dict:
        """Read-only access to container objects."""
        return self._containers

    # ------------------------------------------------------------------ #
    # Stats — for dashboard only                                          #
    # ------------------------------------------------------------------ #

    def get_stats(self) -> dict:
        return {
            "waste_on_streets": int(self._waste_grid.sum()),
            "full_bins":        sum(1 for b in self._bins.values() if b.is_full),
            "full_containers":  sum(1 for c in self._containers.values() if c.is_full),
            "total_deposited":  self.total_deposited,
            "total_cleaned":    self.total_cleaned,
            "total_trips":      self.total_trips,
        }