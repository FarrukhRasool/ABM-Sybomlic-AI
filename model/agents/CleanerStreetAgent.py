from collections import deque
from agents.BaseAgent import BaseAgent


class CleanerStreetAgent(BaseAgent):
    """
    Street-cleaning agent with a predefined patrol route.

    Main behavior:
        - Follow a fixed patrol path
        - Pick up waste found on the current cell
        - When its carrying capacity is full, go to the disposal area
        - Empty its load there
        - Return to the exact patrol interruption point
        - Resume patrol from where it stopped
    """


    # ==================================================================
    # Initialization
    # ==================================================================

    def __init__(
        self,
        model,
        start_pos: tuple,
        disposal_pos: tuple,
        patrol_path: list[tuple],
        capacity: int = 1,
    ):
        super().__init__(model)

        self.start_pos = start_pos
        self.disposal_pos = disposal_pos
        self.capacity = capacity
        self.load = 0

        # Patrol route memory:
        # these variables are used when the cleaner interrupts its patrol
        # to go empty its load, and later returns to the exact same point
        self.resume_target = None
        self.resume_position = None
        self.resume_index = None

        # Predefined patrol route
        self.patrol_path = patrol_path
        self.path_index = 0

        # Current mode:
        # "patrol" -> follow patrol_path
        # "to_disposal" -> go empty
        # "return_to_patrol" -> go back to patrol route
        self.mode = "patrol"

        # Temporary path used when going to disposal / coming back
        self.temp_path = []

        
    # ==================================================================
    # ABM logic: perceive -> decide -> act
    # ==================================================================

    def perceive(self) -> dict:
        """
        Observe the local state relevant to the cleaner's task.
        """
        return {
            "has_waste_here": self.model.waste.has_waste(self.pos),
            "is_full": self.load >= self.capacity,
            "at_disposal": self.pos == self.disposal_pos,
        }

    def decide(self, obs: dict) -> dict:
        """
        Select the next action based on local observations and internal mode.

        Decision priorities:
            1. Pick up waste if present and still carrying space is available
            2. If full, go to disposal or empty if already there
            3. If currently returning from disposal, continue return
            4. Otherwise continue normal patrol
        """
        # Priority 1: collect waste on current cell
        if obs["has_waste_here"] and not obs["is_full"]:
            return {"action": "pick_here"}

        # Priority 2: if full -> go to disposal
        if obs["is_full"]:
            if obs["at_disposal"]:
                return {"action": "empty"}
            return {"action": "go_to_disposal"}

        # Priority 3: return from disposal to patrol
        if self.mode == "return_to_patrol":
            return {"action": "return_to_patrol"}

        # Default: continue patrol
        return {"action": "patrol"}

    def act(self, decision: dict) -> None:
        """
        Execute the selected action.

        Supported actions:
            - pick_here : : pick one unit of waste from the current cell
            - go_to_disposal : save the exact interruption point of the patrol
            - empty : empty carried waste at disposal area
            - return_to_patrol : restore the interruption point
            - patrol : step
        """
        action = decision["action"]

        if action == "pick_here":
            before = self.model.waste.waste_grid[self.pos[0], self.pos[1]]
            picked = self.model.waste.pick_waste(self.pos, 1)
            after = self.model.waste.waste_grid[self.pos[0], self.pos[1]]
            self.load += picked
            # ------------------------------------------------------------
            # Debug : Check if the waste has been collected
            # ------------------------------------------------------------
            print(f"[Cleaner] pos={self.pos} before={before} picked={picked} after={after}")

        elif action == "go_to_disposal":
            if self.mode != "to_disposal":
                self.mode = "to_disposal"

                # Save exact interruption point
                self.resume_position = self.pos
                self.resume_index = self.path_index
                self.resume_target = self.resume_position

                self.temp_path = self._bfs_path(self.pos, self.disposal_pos)

            self._follow_temp_path()

        elif action == "empty":
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
            "[CleanerStreetAgent]",
            "id=", self.unique_id,
            "orientation=", getattr(self, "patrol_orientation", "?"),
            "mode=", self.mode,
            "action=", action,
            "pos=", self.pos,
            "load=", f"{self.load}/{self.capacity}",
            "path_index=", self.path_index
        )
            

    


    
