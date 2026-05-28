# model/agents/BinTransporterAgent.py

from collections import deque
from agents.BaseAgent import BaseAgent
from constants import BIN, CONTAINER


class BinTransporterAgent(BaseAgent):
    """
    Transport agent dedicated to bin waste collection.

    Main behavior:
        - Patrol along a predefined route
        - If standing on a non-empty bin, empty it immediately
        - When full, go to the nearest assigned container
        - Empty the carried load into the container
        - Return to the exact interruption point
        - Resume patrol from where it stopped
    """

    def __init__(
        self,
        model,
        start_pos: tuple,
        patrol_path: list[tuple],
        assigned_bins: list[tuple],
        assigned_containers: list[tuple],
        capacity: int = 5,
    ):
        super().__init__(model)

        self.start_pos = start_pos
        self.patrol_path = patrol_path
        self.assigned_bins = assigned_bins
        self.assigned_containers = assigned_containers

        self.capacity = capacity
        self.load = 0

        # Patrol progress
        self.path_index = 0

        # Current mode:
        self.mode = "patrol"

        # Temporary path
        self.temp_path = []

        # Memory of the exact interruption point
        self.resume_target = None
        self.resume_position = None
        self.resume_index = None

        # Current unloading target container
        self.target_container = None


    # ==================================================================
    # ABM logic: perceive -> decide -> act
    # ==================================================================

    def perceive(self) -> dict:
        """
        Observe the local environment.
        """
        current_bin = self.model.waste.bins.get(self.pos, None)
        current_container = self.model.waste.containers.get(self.pos, None)

        bin_level = current_bin.level if current_bin else 0
        at_bin = current_bin is not None
        at_container = current_container is not None

        return {
            "at_bin": at_bin,
            "bin_level": bin_level,
            "at_container": at_container,
            "is_full": self.load >= self.capacity,
            "has_load": self.load > 0,
        }

    def decide(self, obs: dict) -> dict:
        """
        Select the next action based on local observations and internal mode.

        Decision priorities:
            1. If currently going to a container, continue until unloading
            2. If currently returning to patrol, continue return
            3. If full, leave patrol and go to a container
            4. If standing on a non-empty bin, empty it immediately
            5. Otherwise continue patrol
        """
        if self.mode == "to_container":
            if obs["at_container"]:
                return {"action": "empty_into_container"}
            return {"action": "go_to_container"}

        if self.mode == "return_to_patrol":
            return {"action": "return_to_patrol"}

        # simple rule: if transporter is full, go empty into container
        if obs["is_full"]:
            return {"action": "go_to_container"}

        # simple rule: if standing on a non-empty bin, empty it immediately
        if obs["at_bin"] and obs["bin_level"] > 0:
            return {"action": "empty_bin_here"}

        return {"action": "patrol"}

    def act(self, decision: dict) -> None:
        """
        Execute the selected action.

        Supported actions:
            - empty_bin_here : empty the current bin
            - go_to_container : save the exact interruption point of the patrol
            - empty_into_container : empty carried waste at target container
            - return_to_patrol : restore the interruption point
            - patrol : step
        """
        action = decision["action"]

        if action == "empty_bin_here":
            bin_obj = self.model.waste.bins.get(self.pos)
            if bin_obj is not None and bin_obj.level > 0:
                remaining_capacity = self.capacity - self.load

                if remaining_capacity > 0:
                    # Empty the whole bin, then keep only what fits
                    collected = self.model.waste.empty_bin(self.pos)
                    accepted = min(collected, remaining_capacity)
                    overflow_back = collected - accepted

                    self.load += accepted

                    # If transporter could not take all, put the rest back into the bin
                    if overflow_back > 0:
                        self.model.waste.deposit_to_bin(self.pos, overflow_back)

        elif action == "go_to_container":
            if self.mode != "to_container":
                self.mode = "to_container"

                # Save interruption point
                self.resume_position = self.pos
                self.resume_index = self.path_index
                self.resume_target = self.resume_position

                self.target_container = self._nearest_container(self.pos)
                if self.target_container is not None:
                    self.temp_path = self._bfs_path(self.pos, self.target_container)
                else:
                    self.temp_path = []

            self._follow_temp_path()

        elif action == "empty_into_container":
            if self.target_container is not None and self.load > 0:
                overflow = self.model.waste.deposit_to_container(
                    self.target_container,
                    self.load
                )
                deposited = self.load - overflow
                self.load = overflow

            # if all load deposited, return to patrol
            if self.load == 0:
                self.mode = "return_to_patrol"
                self.temp_path = self._bfs_path(self.pos, self.resume_target)

        elif action == "return_to_patrol":
            if self.pos == self.resume_target:
                self.mode = "patrol"
                self.temp_path = []
                self.target_container = None

                if self.resume_index is not None:
                    self.path_index = self.resume_index
            else:
                if not self.temp_path:
                    self.temp_path = self._bfs_path(self.pos, self.resume_target)
                self._follow_temp_path()

        elif action == "patrol":
            self._patrol_step()

        # ------------------------------------------------------------
        # Debug : Check the states of the agent 
        # ------------------------------------------------------------
        print(
            "[BinTransporterAgent]",
            "id=", self.unique_id,
            "mode=", self.mode,
            "action=", action,
            "pos=", self.pos,
            "load=", f"{self.load}/{self.capacity}",
            "path_index=", self.path_index
        )

    
    # ==================================================================
    # Helper functions
    # ==================================================================

    def _nearest_container(self, start: tuple):
        """
         Return the nearest assigned container to the given position.
        """
        if not self.assigned_containers:
            return None

        return min(
            self.assigned_containers,
            key=lambda p: abs(p[0] - start[0]) + abs(p[1] - start[1])
        )


    

    

