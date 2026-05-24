# model/agents/HumanAgent.py

import random
from agents.BaseAgent import BaseAgent
from constants import *


class HumanAgent(BaseAgent):
    """
    Represents a local resident moving between buildings.
    """

    WASTE_PROBABILITY = 0.10
    MAX_WASTE_PER_TRIP = 3

    def __init__(self, model, start_pos: tuple, destination: tuple):
        super().__init__(model)
        self.destination    = destination
        self.carrying_extra_waste = False
        self.waste_units    = 5 
        self._last_pos      = None  # ← track last pos to avoid oscillation
        self._max_extra_waste       = random.randint(2, 3)
        self._waste_dropped   = 0 

    def perceive(self) -> dict:
        neighbors = self.get_walkable_neighbors()
        adjacent_bins = [
            pos for pos, b in self.model.waste.bins.items()
            if abs(pos[0]-self.pos[0]) + abs(pos[1]-self.pos[1]) <= 1
            and not b.is_full and b.is_active
        ]
        # Find nearest bin
        bins     = self.model.waste.bins
        near_bin = self.get_nearest(
            [pos for pos, b in bins.items() if not b.is_full and b.is_active]
        )

        # Only consider bin if it's close enough (within 5 steps)
        if near_bin and self.get_distance(self.pos, near_bin) > 5:
            near_bin = None

        can_generate = (
            random.random() < self.WASTE_PROBABILITY and
            self._waste_dropped < self._max_extra_waste and 
            not self.carrying_extra_waste
        )

        return {
            "current_cell":   self.get_current_cell_type(),
            "neighbors":      neighbors,
            "at_destination": self.pos == self.destination,
            "adjacent_bins":  adjacent_bins,              
            "has_units":      self.waste_units > 0,       
            "nearest_bin":    near_bin,
            "carrying_extra_waste": self.carrying_extra_waste,
            "generate_waste": random.random() < self.WASTE_PROBABILITY,
        }

    def decide(self, observation: dict) -> dict:

        if observation["at_destination"]:
            return {"action": "disappear"}

        # Passing by a bin AND has anything to deposit → deposit
        if observation["adjacent_bins"] and (
            observation["has_units"] or observation["carrying_extra_waste"]
        ):
            return {
                "action":  "deposit",           # ← one unified action
                "bin_pos": observation["adjacent_bins"][0],
            }

        # Carrying generated waste, no adjacent bin → move toward nearest
        if observation["carrying_extra_waste"]:
            near_bin = observation["nearest_bin"]
            if near_bin:
                return {"action": "move_to_bin", "target": near_bin}
            else:
                return {"action": "drop_waste"}

        # Generate extra waste mid-trip
        if observation["generate_waste"]:
            self.carrying_extra_waste = True
            return {"action": "move", "target": self.destination}

        return {"action": "move", "target": self.destination}


    def _can_drop_more_waste(self) -> bool:
        """Return True if agent is still under waste limit."""
        return self._waste_dropped < self._max_extra_waste

    def act(self, decision: dict) -> None:
        action = decision["action"]

        if action == "disappear":
            self._disappear()

        elif action == "deposit":
            overflow = self.model.waste.deposit_to_bin(decision["bin_pos"], 1)
            
            if overflow == 0:
                # Successfully deposited
                if self.waste_units > 0:
                    self.waste_units -= 1          # ← reduce default units
                elif self.carrying_extra_waste:
                    self.carrying_extra_waste = False    # ← clear extra waste flag
                    # Do NOT increment _waste_dropped here — already counted
            else:
                # Bin full → drop on road
                if self.waste_units > 0:
                    # Drop default unit on road
                    if self.model.waste.is_wasteable(self.pos):
                        self.model.waste.add_waste(self.pos)
                    self.waste_units -= 1
                elif self.carrying_extra_waste and self._can_drop_more_waste():
                    # Drop extra waste on road
                    if self.model.waste.is_wasteable(self.pos):
                        self.model.waste.add_waste(self.pos)
                    self.carrying_extra_waste = False
                    # Do NOT increment _waste_dropped — already counted in generate step

            self._move_toward(self.destination)

        elif action == "drop_waste":
            if self.model.waste.is_wasteable(self.pos) and self._can_drop_more_waste():
                self.model.waste.add_waste(self.pos)
                self._waste_dropped += 1
            self.carrying_extra_waste = False
            self._move_toward(self.destination)

        elif action == "move_to_bin":
            self._move_toward(decision["target"])

        elif action == "move":
            self._move_toward(decision["target"])


    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _move_toward(self, target: tuple) -> None:
        """
        Move one step toward target.
        Avoids oscillation by never stepping back to last position
        unless it's the only option.
        """
        neighbors = self.get_walkable_neighbors()
        if not neighbors:
            return

        # Filter out last position to avoid oscillation
        non_backtrack = [n for n in neighbors if n != self._last_pos]
        candidates    = non_backtrack if non_backtrack else neighbors

        # Pick neighbor closest to target
        best          = min(candidates, key=lambda n: self.get_distance(n, target))
        self._last_pos = self.pos
        self.move_to(best)

    def _disappear(self) -> None:
        """Remove agent from grid and model."""
        self.model.grid.remove_agent(self)
        self.model.agents.remove(self)
        self.is_active = False