# model/agents/base/BaseAgent.py

from mesa import Agent
from abc import ABC, abstractmethod
from constants import *


class BaseAgent(Agent, ABC):
    """
    Abstract base class for all agents in the city simulation.

    Design Pattern:
        Template Method — step() defines the skeleton.
        Subclasses implement perceive(), decide(), act().

    Real-world analogy:
        Every entity in the city follows the same cognitive loop:
        1. Look around        (perceive)
        2. Decide what to do  (decide)
        3. Do it              (act)
    """

    def __init__(self, model):
        super().__init__(model)
        self.is_active = True  # set False to deactivate without removing

    # ------------------------------------------------------------------ #
    # Template Method — do NOT override in subclasses                     #
    # ------------------------------------------------------------------ #

    def step(self) -> None:
        """
        Orchestrates the agent's cognitive loop each simulation step.
        This method is FINAL — subclasses must not override it.
        """
        if not self.is_active:
            return
        observation = self.perceive()
        decision    = self.decide(observation)
        self.act(decision)

    # ------------------------------------------------------------------ #
    # Abstract methods — MUST be implemented by every subclass            #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def perceive(self) -> dict:
        """
        Sense the local environment.
        Returns a dict of observations the agent can see.

        Example return:
        {
            "current_cell":  "road",
            "neighbors":     [(x1,y1), (x2,y2), ...],
            "has_waste":     True,
            "waste_amount":  3,
        }
        """

    @abstractmethod
    def decide(self, observation: dict) -> dict:
        """
        Process observations and choose an action.
        Returns a dict describing the chosen action.

        Example return:
        {
            "action": "move",
            "target": (x+1, y),
        }
        """

    @abstractmethod
    def act(self, decision: dict) -> None:
        """
        Execute the chosen action in the environment.
        Modifies model state — moves, drops waste, cleans, etc.
        """

    # ------------------------------------------------------------------ #
    # Shared helpers — available to ALL subclasses                        #
    # ------------------------------------------------------------------ #

    def get_current_cell_type(self) -> str:
        """Return the cell type at the agent's current position."""
        return self.model.get_cell_type(self.pos)

    def get_walkable_neighbors(self) -> list:
        """
        Return walkable neighboring positions (4 directions only).
        Agents cannot walk through buildings, doors used as entry points.
        """
        neighbors = self.model.grid.get_neighborhood(
            self.pos,
            moore=False,        # Von Neumann — 4 directions only
            include_center=False
        )
        return [n for n in neighbors if self.model.is_walkable(n)]

    def move_to(self, pos: tuple) -> None:
        """Move agent to a new position on the grid."""
        self.model.grid.move_agent(self, pos)

    def get_distance(self, pos_a: tuple, pos_b: tuple) -> int:
        """Manhattan distance between two positions."""
        return abs(pos_a[0] - pos_b[0]) + abs(pos_a[1] - pos_b[1])

    def get_nearest(self, positions: list) -> tuple | None:
        """Return the nearest position from a list using Manhattan distance."""
        if not positions:
            return None
        return min(positions, key=lambda p: self.get_distance(self.pos, p))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.unique_id}, pos={self.pos})"