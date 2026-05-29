# model/agents/base/BaseAgent.py

from mesa import Agent
from abc import ABC, abstractmethod
from constants import *
from collections import deque


class BaseAgent(Agent, ABC):
    """
    Abstract base class for all agents in the city simulation.

    Design Pattern:
        Template Method — step() defines the skeleton.
        Subclasses implement perceive(), decide(), act().

    It provides:
            - a shared control loop (`step`)
            - common movement/navigation helpers
            - utility functions reused by multiple agent types

    Real-world analogy:
        Every entity in the city follows the same cognitive loop:
        1. Look around        (perceive)
        2. Decide what to do  (decide)
        3. Do it              (act)
    """


    # ==================================================================
    # Initialization
    # ==================================================================

    def __init__(self, model):
        super().__init__(model)
        self.is_active = True  # set False to deactivate without removing

    
    # ==================================================================
    # Template Method: common perception-decision-action loop
    # ==================================================================

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


    # ==================================================================
    # Abstract methods: must be implemented by subclasses
    # ==================================================================

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

    # ==================================================================
    # General helper methods shared by all agents
    # ==================================================================

    def get_current_cell_type(self) -> str:
        """Return the cell type at the agent's current position."""
        return self.model.get_cell_type(self.pos)

    # Delete function ? 
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
    

    # ==================================================================
    # Temporary-path following helper
    # ==================================================================

    def _follow_temp_path(self) -> None:
        """
        Follow one step of the temporary BFS path.
        """
        if not self.temp_path:
            return

        # Remove current cell if present as first element
        if self.temp_path and self.temp_path[0] == self.pos:
            self.temp_path.pop(0)

        if not self.temp_path:
            return

        next_pos = self.temp_path.pop(0)
        self.move_to(next_pos)


    # ==================================================================
    # BFS helpers
    # ==================================================================

    def _bfs_path(self, start: tuple, goal: tuple) -> list[tuple]:
        """
        Compute a shortest walkable path from start to goal using BFS.

        Notes:
            - The returned path includes both start and goal
            - Returns an empty list if no path exists
        """
        if goal is None:
            return []
        
        if start == goal:
            return [start]

        queue = deque([start])
        visited = {start}
        parents = {start: None}

        while queue:
            current = queue.popleft()

            for neighbor in self._walkable_neighbors(current):
                if neighbor in visited:
                    continue

                visited.add(neighbor)
                parents[neighbor] = current

                if neighbor == goal:
                    return self._reconstruct_path(parents, goal)

                queue.append(neighbor)

        return []

    def _walkable_neighbors(self, pos: tuple) -> list[tuple]:
        """
        Return all valid walkable 4-neighbors of a given position.
        """
        x, y = pos
        candidates = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1),
        ]

        valid = []
        for nx, ny in candidates:
            if 0 <= nx < self.model.grid.width and 0 <= ny < self.model.grid.height:
                if self.model.is_walkable((nx, ny)):
                    valid.append((nx, ny))
        return valid

    def _reconstruct_path(self, parents: dict, goal: tuple) -> list[tuple]:
        """
        Reconstruct a BFS path from the parent dictionary.
        """
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = parents[current]
        path.reverse()
        return path


    # ==================================================================
    # Small helpers
    # ==================================================================

    def _is_adjacent(self, a: tuple, b: tuple) -> bool:
        """
        Check whether two cells are directly adjacent in 4-neighborhood.
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
    

    # ==================================================================
    # Patrol logic
    # ==================================================================

    def _patrol_step(self) -> None:
        """
        Move one step along the predefined patrol route.

        Behavior:
            - If already at the current patrol target, advance to the next one
            - If the next patrol target is adjacent, move directly
            - Otherwise, compute a short recovery path using BFS
        """
        if not self.patrol_path:
            return

        target = self.patrol_path[self.path_index]

        # If already at target, advance index first
        if self.pos == target:
            self.path_index = (self.path_index + 1) % len(self.patrol_path)
            target = self.patrol_path[self.path_index]

        # Move one step directly if next target is adjacent
        if self._is_adjacent(self.pos, target):
            self.move_to(target)
        else:
            # Safety: if somehow not adjacent, use BFS
            path = self._bfs_path(self.pos, target)
            if len(path) >= 2:
                self.move_to(path[1])