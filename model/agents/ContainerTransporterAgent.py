from collections import deque
from agents.BaseAgent import BaseAgent


class ContainerTransporterAgent(BaseAgent):
    """
    Transport agent dedicated to container-level waste collection.

    Main behavior:
        - Patrol from one container to another
        - If standing on a non-empty container, empty it immediately
        - When full, go to the disposal area
        - Empty the carried load there
        - Return to the exact interruption point
        - Resume patrol from where it stopped
    """


    # ==================================================================
    # Initialization
    # ==================================================================
    def __init__(
        self,
        model,
        start_pos: tuple[int, int],
        patrol_path: list[tuple[int, int]],
        assigned_containers: list[tuple[int, int]],
        disposal_pos: tuple[int, int],
        capacity: int = 30,
    ):
        super().__init__(model)

        self.start_pos = start_pos
        self.patrol_path = patrol_path
        self.assigned_containers = assigned_containers
        self.disposal_pos = disposal_pos

        self.capacity = capacity
        self.load = 0

        # Patrol progress
        self.path_index = 0

        # Current activity mode
        self.mode = "patrol"
        
        # Temporary path
        self.temp_path = []

        # Memory of the interruption point
        self.resume_target = None
        self.resume_position = None
        self.resume_index = None


    # ==================================================================
    # ABM logic: perceive -> decide -> act
    # ==================================================================

    def perceive(self) -> dict:
        """
        Observe the local environment.
        """
        current_container = self.model.waste.containers.get(self.pos, None)
        container_level = current_container.level if current_container else 0

        return {
            "at_container": current_container is not None,
            "container_level": container_level,
            "at_disposal": self.pos == self.disposal_pos,
            "is_full": self.load >= self.capacity,
            "has_load": self.load > 0,
        }

    def decide(self, obs: dict) -> dict:
        """
        Select the next action based on local observations and internal mode.

        Decision priorities:
            1. If currently going to disposal, continue that task
            2. If currently returning to patrol, continue returning
            3. If full, leave patrol and go to disposal
            4. If standing on a non-empty container, empty it
            5. Otherwise continue normal patrol
        """
        if self.mode == "to_disposal":
            if obs["at_disposal"]:
                return {"action": "empty_at_disposal"}
            return {"action": "go_to_disposal"}

        if self.mode == "return_to_patrol":
            return {"action": "return_to_patrol"}

        if obs["is_full"]:
            return {"action": "go_to_disposal"}

        if obs["at_container"] and obs["container_level"] > 0:
            return {"action": "empty_container_here"}

        return {"action": "patrol"}

    def act(self, decision: dict) -> None:
        """
        Execute the selected action.

        Supported actions:
            - empty_container_here :  empty the current container
            - go_to_disposal : save the exact interruption point of the patrol
            - empty_at_disposal : empty carried waste at disposal area
            - return_to_patrol : restore the interruption point
            - patrol : step
        """
        action = decision["action"]

        if action == "empty_container_here":
            container_obj = self.model.waste.containers.get(self.pos)

            if container_obj is not None and container_obj.level > 0:
                remaining_capacity = self.capacity - self.load

                if remaining_capacity > 0:
                    collected = self.model.waste.empty_container(self.pos)
                    accepted = min(collected, remaining_capacity)
                    overflow_back = collected - accepted

                    self.load += accepted

                    # If transporter cannot carry everything, put the rest back
                    if overflow_back > 0:
                        self.model.waste.deposit_to_container(self.pos, overflow_back)

        elif action == "go_to_disposal":
            if self.mode != "to_disposal":
                self.mode = "to_disposal"

                # Save exact interruption point
                self.resume_position = self.pos
                self.resume_index = self.path_index
                self.resume_target = self.resume_position

                # Compute a shortest path to disposal
                self.temp_path = self._bfs_path(self.pos, self.disposal_pos)

            self._follow_temp_path()

        elif action == "empty_at_disposal":
            self.load = 0
            self.mode = "return_to_patrol"
            self.temp_path = self._bfs_path(self.pos, self.resume_target)

        elif action == "return_to_patrol":
            if self.pos == self.resume_target:
                self.mode = "patrol"
                self.temp_path = []

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
            "[ContainerTransporterAgent]",
            "id=", self.unique_id,
            "mode=", self.mode,
            "action=", action,
            "pos=", self.pos,
            "load=", f"{self.load}/{self.capacity}",
            "path_index=", self.path_index
        )

    