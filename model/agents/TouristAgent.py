# model/agents/TouristAgent.py

import random
from agents.BaseAgent import BaseAgent
from constants import *


class TouristAgent(BaseAgent):
    """
    Tourist agent visiting the city.

    Main behavior:
        - Spawn in the attractive/tourist area
        - Wander semi-randomly with a preference for attractive cells
        - Generate waste with a higher probability than local humans
        - Try to use a nearby bin when carrying waste
        - Drop waste on the ground if no suitable bin is available
        - Leave the simulation after a limited visit duration
    """

    WASTE_PROBABILITY = 0.20       # double human's 10%
    PARK_ATTRACTION   = 0.70       # 70% chance to move toward park cell
    VISIT_DURATION    = 50         # steps before tourist leaves
    MAX_WASTE_MIN     = 3
    MAX_WASTE_MAX     = 5


    # ==================================================================
    # Initialization
    # ==================================================================
    def __init__(self, model, start_pos: tuple):
        super().__init__(model)
        self.carrying_extra_waste  = False
        self._last_pos       = None
        self._steps_taken    = 0                                    # visit timer
        self._max_extra_waste      = random.randint(
            self.MAX_WASTE_MIN, self.MAX_WASTE_MAX
        )
        self._waste_dropped  = 0


    # ==================================================================
    # ABM logic: perceive -> decide -> act
    # ==================================================================

    def perceive(self) -> dict:
        """
        Observe the local environment.
        """
        neighbors     = self._walkable_neighbors(self.pos) #get_walkable_neighbors()

        # Split neighbors into park and non-park
        park_neighbors = [
            n for n in neighbors
            if self.model.get_cell_type(n) == ATTRACTIVE
        ]
        road_neighbors = [n for n in neighbors if n not in park_neighbors]

        # Find nearest bin
        bins     = self.model.waste.bins
        near_bin = self.get_nearest(
            [pos for pos, b in bins.items() if not b.is_full and b.is_active]
        )
        if near_bin and self.get_distance(self.pos, near_bin) > 5:
            near_bin = None

        can_generate = (
            random.random() < self.WASTE_PROBABILITY and
            self._waste_dropped < self._max_extra_waste and
            not self.carrying_extra_waste
        )

        return {
            "current_cell":    self.get_current_cell_type(),
            "neighbors":       neighbors,
            "park_neighbors":  park_neighbors,
            "road_neighbors":  road_neighbors,
            "visit_over":      self._steps_taken >= self.VISIT_DURATION,
            "nearest_bin":     near_bin,
            "carrying_extra_waste":  self.carrying_extra_waste,
            "generate_waste":  can_generate,
        }

    def decide(self, observation: dict) -> dict:
        """
        Select the next action based on local observations and internal mode.

        Decision priorities:
            1. If the visit is over -> disappear
            2. If waste is generated and a bin is nearby -> move toward the bin
            3. If waste is generated and no bin is nearby -> drop waste
            4. If already carrying waste and at a bin -> deposit
            5. If already carrying waste and a bin exists -> move toward it
            6. If already carrying waste and no bin exists -> drop waste
            7. Otherwise, continue wandering with attraction toward park cells
        """
        # Visit is over → disappear
        if observation["visit_over"]:
            return {"action": "disappear"}

        # Generate waste this step
        if observation["generate_waste"]:
            bin_pos = observation["nearest_bin"]
            if bin_pos:
                self.carrying_extra_waste = True
                return {"action": "move_to_bin", "target": bin_pos}
            else:
                return {"action": "drop_waste"}

        # Already carrying waste
        if observation["carrying_extra_waste"]:
            bin_pos = observation["nearest_bin"]
            if bin_pos and self.pos == bin_pos:
                return {"action": "deposit_bin", "bin_pos": bin_pos}
            elif bin_pos:
                return {"action": "move_to_bin", "target": bin_pos}
            else:
                return {"action": "drop_waste"}

        # Default — wander with park attraction
        return {
            "action":          "wander",
            "park_neighbors":  observation["park_neighbors"],
            "road_neighbors":  observation["road_neighbors"],
            "neighbors":       observation["neighbors"],
        }

    def act(self, decision: dict) -> None:
        """
        Execute the selected action.

        Supported actions:
            - disappear : remove the agent
            - drop_waste : drop waste on the current cell if the surface allows it
            - move_to_bin : move one step toward the target bin
            - deposit_bin : deposit one unit into the bin
            - wander : continue biased random exploration
        """
        action = decision["action"]
        self._steps_taken += 1

        if action == "disappear":
            self._disappear()

        elif action == "drop_waste":
            if self.model.waste.is_wasteable(self.pos) and self._can_drop_more():
                self.model.waste.add_waste(self.pos)
                self._waste_dropped += 1
            self.carrying_extra_waste = False
            self._wander(
                decision.get("park_neighbors", []),
                decision.get("road_neighbors", []),
                decision.get("neighbors", self._walkable_neighbors(self.pos)) #get_walkable_neighbors()),
            )

        elif action == "move_to_bin":
            self._move_toward(decision["target"])

        elif action == "deposit_bin":
            overflow = self.model.waste.deposit_to_bin(decision["bin_pos"], 1)
            if overflow > 0:
                if self.model.waste.is_wasteable(self.pos) and self._can_drop_more():
                    self.model.waste.add_waste(self.pos)
                    self._waste_dropped += 1
            self.carrying_extra_waste = False

        elif action == "wander":
            self._wander(
                decision["park_neighbors"],
                decision["road_neighbors"],
                decision["neighbors"],
            )
        
        # ------------------------------------------------------------
        # Debug : Check the states of the agent
        # ------------------------------------------------------------
        # print(
        #     "[TouristAgent]",
        #     "id=", self.unique_id,
        #     "action=", action,
        #     "pos=", self.pos,
        #     "load=", self.carrying_waste,
        #     "steps_taken=", self._steps_taken,
        #     "waste_dropped=", self._waste_dropped
        # )

    # ==================================================================
    # Internal helpers
    # ==================================================================

    def _can_drop_more(self) -> bool:
        return self._waste_dropped < self._max_extra_waste

    def _wander(self, park_neighbors: list, road_neighbors: list, all_neighbors: list) -> None:
        """
        Move randomly with bias toward park cells.
        70% chance to move to a park neighbor if available.
        30% chance to move to a road neighbor.
        Avoids backtracking.
        """
        if not all_neighbors:
            return

        # Remove last position to avoid oscillation
        park_candidates = [n for n in park_neighbors if n != self._last_pos]
        road_candidates = [n for n in road_neighbors if n != self._last_pos]
        all_candidates  = [n for n in all_neighbors  if n != self._last_pos]

        # Fallback if all candidates filtered out
        if not all_candidates:
            all_candidates = all_neighbors

        # Biased random choice
        if park_candidates and random.random() < self.PARK_ATTRACTION:
            chosen = random.choice(park_candidates)
        elif road_candidates:
            chosen = random.choice(road_candidates)
        else:
            chosen = random.choice(all_candidates)

        self._last_pos = self.pos
        self.move_to(chosen)

    def _move_toward(self, target: tuple) -> None:
        """
        Move one step toward target avoiding backtracking.
        """
        neighbors = self._walkable_neighbors(self.pos) #get_walkable_neighbors()
        if not neighbors:
            return
        non_backtrack = [n for n in neighbors if n != self._last_pos]
        candidates    = non_backtrack if non_backtrack else neighbors
        best          = min(candidates, key=lambda n: self.get_distance(n, target))
        self._last_pos = self.pos
        self.move_to(best)

    def _disappear(self) -> None:
        """
        Remove tourist after visit duration.
        """
        self.model.grid.remove_agent(self)
        self.remove()
        self.is_active = False