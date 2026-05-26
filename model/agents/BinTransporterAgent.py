# model/agents/BinTransporterAgent.py

from collections import deque
from agents.BaseAgent import BaseAgent
from constants import BIN, CONTAINER


class BinTransporterAgent(BaseAgent):
    """
    Simple transporter:
    - patrols on a predefined path
    - if standing on a non-empty bin, empties it immediately
    - when full, goes to nearest assigned container
    - empties load into container
    - returns to interruption point and resumes patrol
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

        self.path_index = 0
        self.mode = "patrol"

        self.temp_path = []
        self.resume_target = None
        self.resume_position = None
        self.resume_index = None

        self.target_container = None

    # ------------------------------------------------------------------
    # ABM logic
    # ------------------------------------------------------------------

    def perceive(self) -> dict:
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

        #print(
            #"[BinTransporterAgent]",
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
    # Temporary path following
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
    # Helpers
    # ------------------------------------------------------------------

    def _nearest_container(self, start: tuple):
        if not self.assigned_containers:
            return None

        return min(
            self.assigned_containers,
            key=lambda p: abs(p[0] - start[0]) + abs(p[1] - start[1])
        )

    def _bfs_path(self, start: tuple, goal: tuple) -> list[tuple]:
        if goal is None:
            return []

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

    def _is_adjacent(self, a: tuple, b: tuple) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1