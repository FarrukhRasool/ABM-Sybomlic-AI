# model/factory/AgentFactory.py

import random
from constants import *


class AgentFactory:
    """
    Factory Pattern — creates and places agents on the model.

    Real-world analogy:
        A city population registry that assigns
        residents to buildings and routes.
    """

    def __init__(self, model):
        self.model = model
        self._door_positions = self._find_doors()

    def _find_doors(self) -> list:
        """Scan grid and collect all door positions."""
        doors = []
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if self.model.get_cell_type((x, y)) == DOOR:
                    doors.append((x, y))
        return doors

    def spawn_human(self) -> None:
        """
        Spawn a HumanAgent at a random door heading to another random door.
        Start and destination must be different doors.
        """
        from agents.HumanAgent import HumanAgent

        if len(self._door_positions) < 2:
            return

        start, destination = random.sample(self._door_positions, 2)

        agent = HumanAgent(
            model       = self.model,
            start_pos   = start,
            destination = destination,
        )
        self.model.grid.place_agent(agent, start)

    def spawn_humans(self, count: int) -> None:
        """Spawn multiple human agents."""
        for _ in range(count):
            self.spawn_human()

    def spawn_tourist(self) -> None:
        """Spawn a tourist at a random park (attractive) cell."""
        from agents.TouristAgent import TouristAgent

        # Find all attractive cells
        park_cells = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if self.model.get_cell_type((x, y)) == ATTRACTIVE
        ]

        if not park_cells:
            return

        start = random.choice(park_cells)
        agent = TouristAgent(model=self.model, start_pos=start)
        self.model.grid.place_agent(agent, start)

    def spawn_tourists(self, count: int) -> None:
        for _ in range(count):
            self.spawn_tourist()

    def respawn_tourists_if_needed(self, minimum: int = 5) -> None:
        from agents.TouristAgent import TouristAgent
        current = sum(1 for a in self.model.agents if isinstance(a, TouristAgent))
        if current < minimum:
            self.spawn_tourists(minimum - current)