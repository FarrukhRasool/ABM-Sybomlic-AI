# model/agents/HumanAgent.py

import random
from agents.BaseAgent import BaseAgent
from constants import *


class HumanAgent(BaseAgent):
    """
    Local resident agent moving from one building entrance to another.

    Main behavior:
        - Move toward a fixed destination
        - Occasionally generate waste
        - If a nearby bin is available, carry the waste toward it
        - Otherwise, drop the waste on the road
        - Disappear when the destination is reached
    """

    WASTE_PROBABILITY = 0.10
    MAX_WASTE_PER_TRIP = 3


    # ==================================================================
    # Initialization
    # ==================================================================
    def __init__(self, model, start_pos: tuple, destination: tuple):
        super().__init__(model)
        self.destination    = destination
        self.carrying_waste = False
        self._last_pos      = None  # ← track last pos to avoid oscillation
        self._max_waste       = random.randint(2, 3)
        self._waste_dropped   = 0 


    # ==================================================================
    # ABM logic: perceive -> decide -> act
    # ==================================================================

    def perceive(self) -> dict:
        """
        Observe the local state relevant to the cleaner's task.
        """
        neighbors = self._walkable_neighbors(self.pos) #get_walkable_neighbors()

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
            self._waste_dropped < self._max_waste and 
            not self.carrying_waste
        )

        return {
            "current_cell":   self.get_current_cell_type(),
            "neighbors":      neighbors,
            "at_destination": self.pos == self.destination,
            "nearest_bin":    near_bin,
            "carrying_waste": self.carrying_waste,
            "generate_waste": random.random() < self.WASTE_PROBABILITY,
        }

    def decide(self, observation: dict) -> dict:
        """
        Select the next action based on local observations and internal mode.

        Decision priorities:
            1. If destination reached -> disappear
            2. If waste is generated and a bin is nearby -> move toward bin
            3. If waste is generated and no bin is nearby -> drop waste
            4. If already carrying waste and at a bin -> deposit into bin
            5. If already carrying waste and bin exists -> move toward bin
            6. If already carrying waste and no bin exists -> drop waste
            7. Otherwise continue toward destination
        """
        # Reached destination → disappear
        if observation["at_destination"]:
            return {"action": "disappear"}

        # Generate waste this step
        if observation["generate_waste"] and not observation["carrying_waste"]:
            bin_pos = observation["nearest_bin"]
            if bin_pos:
                # Bin nearby — carry waste toward it
                self.carrying_waste = True
                return {"action": "move_to_bin", "target": bin_pos}
            else:
                # No bin nearby — drop immediately
                return {"action": "drop_waste"}

        # Already carrying waste
        if observation["carrying_waste"]:
            bin_pos = observation["nearest_bin"]
            if bin_pos and self.pos == bin_pos:
                # Standing at bin — deposit
                return {"action": "deposit_bin", "bin_pos": bin_pos}
            elif bin_pos:
                # Move toward bin
                return {"action": "move_to_bin", "target": bin_pos}
            else:
                # No bin available — drop on road
                return {"action": "drop_waste"}

        # Default — move toward destination
        return {"action": "move", "target": self.destination}

    def act(self, decision: dict) -> None:
        """
        Execute the selected action.

        Supported actions:
            - disappear : human delete
            - drop_waste : drop waste on the current cell if the surface allows it
            - move_to_bin : move one step toward the target bin
            - deposit_bin : deposit one unit into the bin
            - move : continue moving toward the destination
        """
        action = decision["action"]

        if action == "disappear":
            self._disappear()

        elif action == "drop_waste":
            if self.model.waste.is_wasteable(self.pos) and self._can_drop_more_waste():
                self.model.waste.add_waste(self.pos)
                self._waste_dropped += 1
            self.carrying_waste = False
            self._move_toward(self.destination)

        elif action == "move_to_bin":
            self._move_toward(decision["target"])

        elif action == "deposit_bin":
            overflow = self.model.waste.deposit_to_bin(decision["bin_pos"], 1)
            if overflow > 0:
                if self.model.waste.is_wasteable(self.pos) and self._can_drop_more_waste():
                    self.model.waste.add_waste(self.pos)
                    self._waste_dropped += 1
            self.carrying_waste = False
            self._move_toward(self.destination)

        elif action == "move":
            self._move_toward(decision["target"])

        # ------------------------------------------------------------
        # Debug : Check the states of the agent 
        # ------------------------------------------------------------
        print(
            "[HumanAgent]",
            "id=", self.unique_id,
            "action=", action,
            "pos=", self.pos,
            "destination=", self.destination,
            "carrying_waste=", self.carrying_waste,
            "waste_dropped=", self._waste_dropped
        )


    # ==================================================================
    # Internal helpers
    # ==================================================================
    def _can_drop_more_waste(self) -> bool:
        """
        Return True if agent is still under waste limit.
        """
        return self._waste_dropped < self._max_waste

    def _move_toward(self, target: tuple) -> None:
        """
        Move one step toward a target position.

        Strategy:
            - consider all walkable neighbors
            - avoid immediately returning to the previous position if possible
            - choose the neighbor with minimum Manhattan distance to target
        """
        neighbors = self._walkable_neighbors(self.pos) #get_walkable_neighbors()
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
        """
        Remove agent from grid and model.
        """
        self.model.grid.remove_agent(self)
        self.model.agents.remove(self)
        self.is_active = False