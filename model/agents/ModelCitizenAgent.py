# model/agents/ModelCitizenAgent.py

import random
from agents.BaseAgent import BaseAgent
from constants import WASTE


class ModelCitizenAgent(BaseAgent):
    """
    A prosocial citizen:
    - wanders randomly through the city
    - picks up waste on the ground
    - when full, goes to the nearest available bin
    - empties load into the bin
    - resumes wandering
    """

    def __init__(self, model, start_pos: tuple[int, int], capacity: int = 3):
        super().__init__(model)

        self.start_pos = start_pos
        self.capacity = capacity
        self.load = 0

        self.mode = "wander"   # wander / to_bin
        self._last_pos = None

    # ------------------------------------------------------------------
    # ABM logic
    # ------------------------------------------------------------------

    def perceive(self) -> dict:
        neighbors = self.get_walkable_neighbors()

        # nearest available bin
        available_bins = [
            pos for pos, b in self.model.waste.bins.items()
            if b.is_active and not b.is_full
        ]
        nearest_bin = self.get_nearest(available_bins)

        return {
            "neighbors": neighbors,
            "has_waste_here": self.model.waste.has_waste(self.pos),
            "is_full": self.load >= self.capacity,
            "has_load": self.load > 0,
            "at_bin": self.pos in self.model.waste.bins,
            "nearest_bin": nearest_bin,
        }

    def decide(self, obs: dict) -> dict:
        # If full, try to go to a bin
        if obs["is_full"]:
            if obs["at_bin"]:
                return {"action": "deposit_here"}

            if obs["nearest_bin"] is not None:
                return {"action": "go_to_bin", "target": obs["nearest_bin"]}

            # no available bin: keep wandering
            return {"action": "wander"}

        # If not full and standing on waste, pick it up
        if obs["has_waste_here"]:
            return {"action": "pick_here"}

        # If carrying some waste and standing on a bin, deposit
        if obs["has_load"] and obs["at_bin"]:
            return {"action": "deposit_here"}

        # Default behavior: wander
        return {"action": "wander"}

    def act(self, decision: dict) -> None:
        action = decision["action"]

        if action == "pick_here":
            remaining_capacity = self.capacity - self.load
            picked = self.model.waste.pick_waste(self.pos, remaining_capacity)
            self.load += picked

        elif action == "go_to_bin":
            self._move_toward(decision["target"])

        elif action == "deposit_here":
            if self.pos in self.model.waste.bins and self.load > 0:
                overflow = self.model.waste.deposit_to_bin(self.pos, self.load)
                deposited = self.load - overflow
                self.load = overflow

            # if everything was deposited, return to wandering
            if self.load == 0:
                self.mode = "wander"

        elif action == "wander":
            self._wander()

        print(
            "[ModelCitizenAgent]",
            "id=", self.unique_id,
            "mode=", self.mode,
            "action=", action,
            "pos=", self.pos,
            "load=", f"{self.load}/{self.capacity}"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _wander(self) -> None:
        """
        Random movement with light anti-oscillation.
        """
        neighbors = self.get_walkable_neighbors()
        if not neighbors:
            return

        non_backtrack = [n for n in neighbors if n != self._last_pos]
        candidates = non_backtrack if non_backtrack else neighbors

        chosen = random.choice(candidates)
        self._last_pos = self.pos
        self.move_to(chosen)

    def _move_toward(self, target: tuple[int, int]) -> None:
        """
        Greedy one-step movement toward target, avoiding immediate backtracking.
        """
        neighbors = self.get_walkable_neighbors()
        if not neighbors:
            return

        non_backtrack = [n for n in neighbors if n != self._last_pos]
        candidates = non_backtrack if non_backtrack else neighbors

        best = min(candidates, key=lambda n: self.get_distance(n, target))
        self._last_pos = self.pos
        self.move_to(best)