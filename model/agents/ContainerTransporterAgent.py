from collections import deque
from agents.BaseAgent import BaseAgent


class ContainerTransporterAgent(BaseAgent):
    """
    Transporter that patrols from container to container.
    - If standing on a non-empty container, empties it immediately
    - When full, goes to disposal area
    - Empties load there
    - Returns to interruption point and resumes patrol
    """

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

        self.path_index = 0
        self.mode = "patrol"

        self.temp_path = []
        self.resume_target = None
        self.resume_position = None
        self.resume_index = None

    # ------------------------------------------------------------------
    # ABM logic
    # ------------------------------------------------------------------

    def perceive(self) -> dict:
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

        #print(
            #"[ContainerTransporterAgent]",
            #"id=", self.unique_id,
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
        if not self.patrol_path:
            return

        target = self.patrol_path[self.path_index]

        if self.pos == target:
            self.path_index = (self.path_index + 1) % len(self.patrol_path)
            target = self.patrol_path[self.path_index]

        if self._is_adjacent(self.pos, target):
            self.move_to(target)
        else:
            path = self._bfs_path(self.pos, target)
            if len(path) >= 2:
                self.move_to(path[1])

    # ------------------------------------------------------------------
    # Temporary path
    # ------------------------------------------------------------------

    def _follow_temp_path(self) -> None:
        if not self.temp_path:
            return

        if self.temp_path and self.temp_path[0] == self.pos:
            self.temp_path.pop(0)

        if not self.temp_path:
            return

        next_pos = self.temp_path.pop(0)
        self.move_to(next_pos)

    # ------------------------------------------------------------------
    # BFS helpers
    # ------------------------------------------------------------------

    def _bfs_path(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
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

    def _walkable_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
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

    def _reconstruct_path(self, parents: dict, goal: tuple[int, int]) -> list[tuple[int, int]]:
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = parents[current]
        path.reverse()
        return path

    def _is_adjacent(self, a: tuple[int, int], b: tuple[int, int]) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1