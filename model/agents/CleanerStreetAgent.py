from collections import deque
from agents.BaseAgent import BaseAgent


class CleanerStreetAgent(BaseAgent):
    """
    CleanerStreetAgent with a predefined patrol path.

    Behavior:
    - Follow patrol_path cell by cell
    - Collect waste found on the current cell
    - When full, go to disposal area
    - Empty load
    - Return to patrol and continue where it stopped
    """

    def __init__(
        self,
        model,
        start_pos: tuple,
        disposal_pos: tuple,
        patrol_path: list[tuple],
        capacity: int = 5,
    ):
        super().__init__(model)

        self.start_pos = start_pos
        self.disposal_pos = disposal_pos
        self.capacity = capacity
        self.load = 0

        # Memory of position
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

        # Patrol resume target
        self.resume_target = None

    # ------------------------------------------------------------------
    # ABM logic
    # ------------------------------------------------------------------

    def perceive(self) -> dict:
        return {
            "has_waste_here": self.model.waste.has_waste(self.pos),
            "is_full": self.load >= self.capacity,
            "at_disposal": self.pos == self.disposal_pos,
        }

    def decide(self, obs: dict) -> dict:
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
        action = decision["action"]

        if action == "pick_here":
            before = self.model.waste.waste_grid[self.pos[0], self.pos[1]]
            picked = self.model.waste.pick_waste(self.pos, 1)
            after = self.model.waste.waste_grid[self.pos[0], self.pos[1]]
            self.load += picked
            #print(f"[Cleaner] pos={self.pos} before={before} picked={picked} after={after}")

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

        #print(
            #"[CleanerStreetAgent]",
            #"id=", self.unique_id,
            #"orientation=", getattr(self, "patrol_orientation", "?"),
            #"mode=", self.mode,
            #"action=", action,
            #"pos=", self.pos,
            #"load=", f"{self.load}/{self.capacity}",
            #"path_index=", self.path_index
        #)
            

    # ------------------------------------------------------------------
    # Patrol logic
    # ------------------------------------------------------------------

    def _patrol_step(self) -> None:
        """
        Move to the next cell in the predefined patrol path.
        Cycles when reaching the end.
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

    # ------------------------------------------------------------------
    # Temporary path following (disposal / return)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # BFS helpers
    # ------------------------------------------------------------------

    def _bfs_path(self, start: tuple, goal: tuple) -> list[tuple]:
        """
        Returns a shortest walkable path from start to goal.
        Includes start and goal in the list.
        Returns [] if no path exists.
        """
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
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = parents[current]
        path.reverse()
        return path

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    def _is_adjacent(self, a: tuple, b: tuple) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1
