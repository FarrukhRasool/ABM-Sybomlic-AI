# model/factory/AgentFactory.py

import random
from constants import *
from agents.CleanerStreetAgent import CleanerStreetAgent
from agents.BinTransporterAgent import BinTransporterAgent
from agents.ContainerTransporterAgent import ContainerTransporterAgent
from agents.ModelCitizenAgent import ModelCitizenAgent


class AgentFactory:
    """
    Factory Pattern — creates and places agents on the model.

    Real-world analogy:
        A city population registry that assigns
        residents to buildings and routes.
    """

    def __init__(self, model):
        self.model = model
        self._door_positions = self._find_doors()
        self._disposal_positions = self._find_disposal()

    def _find_doors(self) -> list:
        """Scan grid and collect all door positions."""
        doors = []
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if self.model.get_cell_type((x, y)) == DOOR:
                    doors.append((x, y))
        return doors
    
    def _find_disposal(self):
        """Scan grid and collect all disposal area positions."""
        disposal = []
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if self.model.get_cell_type((x, y)) == DISPOSAL:
                    disposal.append((x, y))
        return disposal

    def spawn_human(self) -> None:
        """
        Spawn a HumanAgent at a random door heading to another random door.
        Start and destination must be different doors.
        """
        from agents.HumanAgent import HumanAgent

        if len(self._door_positions) < 2:
            return

        start, destination = random.sample(self._door_positions, 2)

        agent = HumanAgent(
            model       = self.model,
            start_pos   = start,
            destination = destination,
        )
        self.model.grid.place_agent(agent, start)

    def spawn_humans(self, count: int) -> None:
        """Spawn multiple human agents."""
        for _ in range(count):
            self.spawn_human()

    def spawn_tourist(self) -> None:
        """Spawn a tourist at a random park (attractive) cell."""
        from agents.TouristAgent import TouristAgent

        # Find all attractive cells
        park_cells = [
            (x, y)
            for x in range(GRID_WIDTH)
            for y in range(GRID_HEIGHT)
            if self.model.get_cell_type((x, y)) == ATTRACTIVE
        ]

        if not park_cells:
            return

        start = random.choice(park_cells)
        agent = TouristAgent(model=self.model, start_pos=start)
        self.model.grid.place_agent(agent, start)

    def spawn_tourists(self, count: int) -> None:
        for _ in range(count):
            self.spawn_tourist()

    def respawn_tourists_if_needed(self, minimum: int = 1) -> None:
        from agents.TouristAgent import TouristAgent
        current = sum(1 for a in self.model.agents if isinstance(a, TouristAgent))
        if current < minimum:
            self.spawn_tourists(minimum - current)

    #def spawn_cleaner_street(self) -> None:
        """Spawn one street cleaner with a start door and a disposal target."""
        #from agents.CleanerStreetAgent import CleanerStreetAgent

        #if not self._door_positions or not self._disposal_positions:
            #return

        #start = random.choice(self._door_positions)
        #destination = random.choice(self._disposal_positions)
        
        #agent = CleanerStreetAgent(
                #model=self.model,
                #start_pos=start,
                #disposal_pos=destination,
        #)
        #self.model.grid.place_agent(agent, start)

    #def spawn_cleaners_street(self, count: int) -> None:
        """Spawn multiple street cleaners."""
        #for _ in range(count):
            #self.spawn_cleaner_street()

    
    #def respawn_cleaners_street_if_needed(self, minimum: int = 1) -> None:
        #"""Maintain at least `minimum` street cleaners alive."""
        #from agents.CleanerStreetAgent import CleanerStreetAgent

        #current = sum(1 for a in self.model.agents if isinstance(a, CleanerStreetAgent))
        #missing = minimum - current
        #if missing > 0:
            #self.spawn_cleaners_street(missing)

    def spawn_cleaner_park(self) -> None:
        """Spawn one street cleaner with a start door and a disposal target."""
        from agents.CleanerParkAgent import CleanerParkAgent

        if not self._door_positions or not self._disposal_positions:
            return

        start = random.choice(self._door_positions)
        destination = random.choice(self._disposal_positions)
        
        agent = CleanerParkAgent(
                model=self.model,
                start_pos=start,
                disposal_pos=destination,
        )
        self.model.grid.place_agent(agent, start)
    
    def spawn_cleaners_park(self, count: int) -> None:
        """Spawn multiple park cleaners."""
        for _ in range(count):
            self.spawn_cleaner_park()

    def respawn_parks_if_needed(self, minimum: int = 1) -> None:
        from agents.CleanerParkAgent import CLeanerParkAgent
        current = sum(1 for a in self.model.agents if isinstance(a, CLeanerParkAgent))
        if current < minimum:
            self.spawn_tourists(minimum - current)


    # ------------------------------------------------------------------
    # Public method: one cleaner per vertical street
    # ------------------------------------------------------------------

    def spawn_one_cleaner_per_vertical_street(self) -> None:
        """
        Detect all vertical streets and spawn one cleaner per street.
        Each cleaner gets a predefined patrol path:
        - down on the left lane
        - up on the right lane
        """
        street_groups = self._find_vertical_street_groups()

        for group in street_groups:
            patrol_path = self._build_vertical_street_patrol_path(group)

            if not patrol_path:
                continue

            start = patrol_path[0]
            disposal = self._nearest_disposal(start)

            if disposal is None:
                continue

            agent = CleanerStreetAgent(
                model=self.model,
                start_pos=start,
                disposal_pos=disposal,
                patrol_path=patrol_path,
            )
            agent.patrol_orientation = "vertical"

            self.model.grid.place_agent(agent, start)

            #print("Cleaner spawned on street:", group)
            #print("Start:", start, "Disposal:", disposal)
            #print("Patrol length:", len(patrol_path))

    # ------------------------------------------------------------------
    # Detect vertical streets
    # ------------------------------------------------------------------

    def _find_vertical_street_groups(self) -> list[list[int]]:
        """
        Return groups of consecutive x-columns that form vertical streets.

        Example output:
        [[3, 4], [17, 18], [31, 32], ...]
        if ROAD_WIDTH = 2
        """
        width = self.model.grid.width
        height = self.model.grid.height

        road_columns = []

        for x in range(width):
            road_count = 0
            for y in range(height):
                if self.model.get_cell_type((x, y)) == ROAD:
                    road_count += 1

            # threshold: true vertical streets have many ROAD cells
            if road_count > height // 3:
                road_columns.append(x)

        # group consecutive x values
        groups = []
        current_group = []

        for x in road_columns:
            if not current_group:
                current_group = [x]
            elif x == current_group[-1] + 1:
                current_group.append(x)
            else:
                groups.append(current_group)
                current_group = [x]

        if current_group:
            groups.append(current_group)

        return groups

    # ------------------------------------------------------------------
    # Build patrol path for one street
    # ------------------------------------------------------------------

    def _build_vertical_street_patrol_path(self, group: list[int]) -> list[tuple]:
        """
        Build path for one vertical street group.

        If the street width is 2:
        - go down on left column
        - go up on right column

        This covers the full street without serpentine.
        """
        if not group:
            return []

        height = self.model.grid.height

        left_x = group[0]
        right_x = group[-1]

        # Downward path on left lane (top -> bottom)
        downward = [
            (left_x, y)
            for y in range(height - 1, -1, -1)
            if self.model.get_cell_type((left_x, y)) == ROAD
        ]

        if not downward:
            return []

        # If street width == 1, just go down then up on same column
        if left_x == right_x:
            upward = list(reversed(downward[1:-1]))
            return downward + upward

        # Upward path on right lane (bottom -> top)
        upward = [
            (right_x, y)
            for y in range(0, height)
            if self.model.get_cell_type((right_x, y)) == ROAD
        ]

        return downward + upward

    # ------------------------------------------------------------------
    # Utility: nearest disposal
    # ------------------------------------------------------------------

    def _nearest_disposal(self, start: tuple):
        if not self._disposal_positions:
            return None

        return min(
            self._disposal_positions,
            key=lambda p: abs(p[0] - start[0]) + abs(p[1] - start[1])
        )
    

    # ------------------------------------------------------------------
    # Detect horizontal streets
    # ------------------------------------------------------------------
    def spawn_one_cleaner_per_horizontal_street(self) -> None:
        """
        Detect all horizontal streets and spawn one cleaner per street.
        Each cleaner gets a predefined patrol path:
        - right on the top lane
        - left on the bottom lane
        """
        street_groups = self._find_horizontal_street_groups()

        for group in street_groups:
            patrol_path = self._build_horizontal_street_patrol_path(group)

            if not patrol_path:
                continue

            start = patrol_path[0]
            disposal = self._nearest_disposal(start)

            if disposal is None:
                continue

            agent = CleanerStreetAgent(
                model=self.model,
                start_pos=start,
                disposal_pos=disposal,
                patrol_path=patrol_path,
            )
            agent.patrol_orientation = "horizontal"

            self.model.grid.place_agent(agent, start)

            #print("Horizontal cleaner spawned on street:", group)
            #print("Start:", start, "Disposal:", disposal)
            #print("Patrol length:", len(patrol_path))
            #print("Horizontal street groups found:", street_groups)
            #print("Horizontal patrol path sample:", patrol_path[:10], "...", patrol_path[-10:])

    def _find_horizontal_street_groups(self) -> list[list[int]]:
        """
        Return groups of consecutive y-rows that form horizontal streets.

        Example output:
        [[3, 4], [17, 18], [31, 32], ...]
        if ROAD_WIDTH = 2
        """
        width = self.model.grid.width
        height = self.model.grid.height

        road_rows = []

        for y in range(height):
            road_count = 0
            for x in range(width):
                if self.model.get_cell_type((x, y)) == ROAD:
                    road_count += 1

            # threshold: true horizontal streets have many ROAD cells
            if road_count > width // 3:
                road_rows.append(y)

        # group consecutive y values
        groups = []
        current_group = []

        for y in road_rows:
            if not current_group:
                current_group = [y]
            elif y == current_group[-1] + 1:
                current_group.append(y)
            else:
                groups.append(current_group)
                current_group = [y]

        if current_group:
            groups.append(current_group)

        return groups
    
    def _build_horizontal_street_patrol_path(self, group: list[int]) -> list[tuple]:
        if not group:
            return []

        width = self.model.grid.width

        top_y = group[0]
        bottom_y = group[-1]

        rightward = [
            (x, top_y)
            for x in range(width)
            if self.model.is_walkable((x, top_y))
        ]

        if not rightward:
            return []

        if top_y == bottom_y:
            leftward = list(reversed(rightward[1:-1]))
            return rightward + leftward

        leftward = [
            (x, bottom_y)
            for x in range(width - 1, -1, -1)
            if self.model.is_walkable((x, bottom_y))
        ]

        return rightward + leftward
    
    def _find_park_vertical_columns(self) -> list[int]:
        """
        Return x-columns that belong to the vertical tourist band.
        """
        width = self.model.grid.width
        height = self.model.grid.height

        columns = []
        for x in range(width):
            attractive_count = sum(
                1 for y in range(height)
                if self.model.get_cell_type((x, y)) == ATTRACTIVE
            )
            if attractive_count >= height // 6:
                columns.append(x)

        return columns
    
    def _find_park_horizontal_rows(self) -> list[int]:
        """
        Return y-rows that belong to the horizontal tourist band.
        """
        width = self.model.grid.width
        height = self.model.grid.height

        rows = []
        for y in range(height):
            attractive_count = sum(
                1 for x in range(width)
                if self.model.get_cell_type((x, y)) == ATTRACTIVE
            )
            if attractive_count >= width // 6:
                rows.append(y)

        return rows
    

    def _build_park_vertical_patrol_path(self, columns: list[int]) -> list[tuple]:
        """
        Build a serpentine patrol path through ATTRACTIVE cells
        for the vertical tourist sector.
        """
        if not columns:
            return []

        height = self.model.grid.height
        path = []
        reverse = False

        for x in columns:
            ys = [
                y for y in range(height)
                if self.model.get_cell_type((x, y)) == ATTRACTIVE
            ]

            if reverse:
                ys.reverse()

            path.extend((x, y) for y in ys)
            reverse = not reverse

        return path
    
    def _build_park_horizontal_patrol_path(self, rows: list[int]) -> list[tuple]:
        """
        Build a serpentine patrol path through ATTRACTIVE cells
        for the horizontal tourist sector.
        """
        if not rows:
            return []

        width = self.model.grid.width
        path = []
        reverse = False

        for y in rows:
            xs = [
                x for x in range(width)
                if self.model.get_cell_type((x, y)) == ATTRACTIVE
            ]

            if reverse:
                xs.reverse()

            path.extend((x, y) for x in xs)
            reverse = not reverse

        return path
    
        # ------------------------------------------------------------------
    # Park cleaners - 5 sectors: north, south, west, east, center
    # ------------------------------------------------------------------

    def _get_attractive_cells(self) -> list[tuple[int, int]]:
        """Return all ATTRACTIVE cells of the city."""
        width = self.model.grid.width
        height = self.model.grid.height

        return [
            (x, y)
            for x in range(width)
            for y in range(height)
            if self.model.get_cell_type((x, y)) == ATTRACTIVE
        ]

    def _find_park_cross_core(self) -> tuple[list[int], list[int]]:
        """
        Detect the central columns and rows of the cross-shaped tourist area.
        Returns:
            center_cols, center_rows
        """
        width = self.model.grid.width
        height = self.model.grid.height

        col_counts = []
        for x in range(width):
            count = sum(
                1 for y in range(height)
                if self.model.get_cell_type((x, y)) == ATTRACTIVE
            )
            col_counts.append(count)

        row_counts = []
        for y in range(height):
            count = sum(
                1 for x in range(width)
                if self.model.get_cell_type((x, y)) == ATTRACTIVE
            )
            row_counts.append(count)

        max_col = max(col_counts) if col_counts else 0
        max_row = max(row_counts) if row_counts else 0

        # central rows/columns = those with highest attractive density
        center_cols = [x for x, c in enumerate(col_counts) if c >= 0.8 * max_col]
        center_rows = [y for y, c in enumerate(row_counts) if c >= 0.8 * max_row]

        return center_cols, center_rows

    def _split_park_into_five_sectors(self) -> dict[str, list[tuple[int, int]]]:
        """
        Split the cross-shaped park into 5 sectors:
        - center
        - north
        - south
        - west
        - east
        """
        attractive_cells = self._get_attractive_cells()
        center_cols, center_rows = self._find_park_cross_core()

        if not attractive_cells or not center_cols or not center_rows:
            return {
                "center": [],
                "north": [],
                "south": [],
                "west": [],
                "east": [],
            }

        min_cx, max_cx = min(center_cols), max(center_cols)
        min_cy, max_cy = min(center_rows), max(center_rows)

        sectors = {
            "center": [],
            "north": [],
            "south": [],
            "west": [],
            "east": [],
        }

        for x, y in attractive_cells:
            if min_cx <= x <= max_cx and min_cy <= y <= max_cy:
                sectors["center"].append((x, y))
            elif min_cx <= x <= max_cx and y > max_cy:
                sectors["north"].append((x, y))
            elif min_cx <= x <= max_cx and y < min_cy:
                sectors["south"].append((x, y))
            elif min_cy <= y <= max_cy and x < min_cx:
                sectors["west"].append((x, y))
            elif min_cy <= y <= max_cy and x > max_cx:
                sectors["east"].append((x, y))

        return sectors

    def _build_serpentine_path_by_columns(
        self,
        cells: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        """
        Build a serpentine path column by column.
        Useful for north/south/center sectors.
        """
        if not cells:
            return []

        columns = {}
        for x, y in cells:
            columns.setdefault(x, []).append(y)

        path = []
        reverse = False

        for x in sorted(columns.keys()):
            ys = sorted(columns[x], reverse=reverse)
            path.extend((x, y) for y in ys)
            reverse = not reverse

        return path

    def _build_serpentine_path_by_rows(
        self,
        cells: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        """
        Build a serpentine path row by row.
        Useful for west/east sectors.
        """
        if not cells:
            return []

        rows = {}
        for x, y in cells:
            rows.setdefault(y, []).append(x)

        path = []
        reverse = False

        for y in sorted(rows.keys()):
            xs = sorted(rows[y], reverse=reverse)
            path.extend((x, y) for x in xs)
            reverse = not reverse

        return path

    def _build_park_sector_patrol_path(
        self,
        sector_name: str,
        cells: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        """
        Build a patrol path adapted to the park sector shape.
        """
        if not cells:
            return []

        if sector_name in ("north", "south", "center"):
            return self._build_serpentine_path_by_columns(cells)

        if sector_name in ("west", "east"):
            return self._build_serpentine_path_by_rows(cells)

        return []

    def spawn_park_cleaners_five_sectors(self, capacity: int = 5) -> None:
        """
        Spawn 5 CleanerParkAgent, one for each park sector:
        center, north, south, west, east.
        """
        from agents.CleanerParkAgent import CleanerParkAgent

        sectors = self._split_park_into_five_sectors()

        print("Park sectors detected:")
        for sector_name, cells in sectors.items():
            print(f"  - {sector_name}: {len(cells)} cells")

        for sector_name, cells in sectors.items():
            patrol_path = self._build_park_sector_patrol_path(sector_name, cells)

            if not patrol_path:
                print(f"No patrol path for park sector: {sector_name}")
                continue

            start = patrol_path[0]
            disposal = self._nearest_disposal(start)

            if disposal is None:
                print(f"No disposal found for park sector: {sector_name}")
                continue

            agent = CleanerParkAgent(
                model=self.model,
                start_pos=start,
                disposal_pos=disposal,
                patrol_path=patrol_path,
                capacity=capacity,
            )

            agent.patrol_orientation = "park"
            agent.park_sector = sector_name

            self.model.grid.place_agent(agent, start)

            #print(f"Park cleaner spawned: sector={sector_name}")
            #print("Start:", start, "Disposal:", disposal)
            #print("Patrol length:", len(patrol_path))

    # ------------------------------------------------------------------
    # Bin transporters by building column
    # ------------------------------------------------------------------

    def _get_building_blocks(self) -> list[tuple[int, int, int, int, int, int]]:
        """
        Return all building blocks as:
        (col_index, row_index, bx_start, bx_end, by_start, by_end)
        """
        blocks = []

        cursor = MARGIN
        road_starts = []
        for i in range(NUM_BLOCKS + 1):
            road_starts.append(cursor)
            cursor += ROAD_WIDTH
            if i < NUM_BLOCKS:
                cursor += BLOCK_SIZE

        building_ranges = [
            (road_starts[i] + ROAD_WIDTH, road_starts[i + 1])
            for i in range(NUM_BLOCKS)
        ]

        mid = NUM_BLOCKS // 2

        for col, (bx_start, bx_end) in enumerate(building_ranges):
            for row, (by_start, by_end) in enumerate(building_ranges):
                # Skip park blocks (same logic as CityGridBuilder)
                if (col == mid and abs(row - mid) <= 1) or \
                   (row == mid and abs(col - mid) <= 1):
                    continue

                blocks.append((col, row, bx_start, bx_end, by_start, by_end))

        return blocks

    def _blocks_for_column(self, target_col: int) -> list[tuple[int, int, int, int, int, int]]:
        """
        Return all building blocks belonging to one building column,
        sorted from top to bottom.
        """
        blocks = [b for b in self._get_building_blocks() if b[0] == target_col]
        return sorted(blocks, key=lambda b: b[5], reverse=True)

    def _build_loop_around_block(
        self,
        bx_start: int,
        bx_end: int,
        by_start: int,
        by_end: int
    ) -> list[tuple[int, int]]:
        """
        Build a patrol loop around one building block using walkable cells.
        """
        candidates = []

        left_x = bx_start - 1
        right_x = bx_end
        bottom_y = by_start - 1
        top_y = by_end

        # bottom edge: left -> right
        for x in range(left_x, right_x + 1):
            candidates.append((x, bottom_y))

        # right edge: bottom+1 -> top
        for y in range(bottom_y + 1, top_y + 1):
            candidates.append((right_x, y))

        # top edge: right-1 -> left
        for x in range(right_x - 1, left_x - 1, -1):
            candidates.append((x, top_y))

        # left edge: top-1 -> bottom+1
        for y in range(top_y - 1, bottom_y, -1):
            candidates.append((left_x, y))

        loop = []
        for pos in candidates:
            x, y = pos
            if 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height:
                if self.model.is_walkable(pos):
                    loop.append(pos)

        return loop

    def _build_building_column_patrol_path(self, target_col: int) -> list[tuple[int, int]]:
        """
        Build a patrol path that loops around each building of one column.
        """
        blocks = self._blocks_for_column(target_col)
        full_path = []

        for _, _, bx_start, bx_end, by_start, by_end in blocks:
            block_loop = self._build_loop_around_block(bx_start, bx_end, by_start, by_end)

            if not block_loop:
                continue

            full_path.extend(block_loop)

        return full_path

    def _bins_for_building_column(self, target_col: int) -> list[tuple[int, int]]:
        """
        Return bins close to buildings of one column.
        """
        blocks = self._blocks_for_column(target_col)
        assigned = set()

        for _, _, bx_start, bx_end, by_start, by_end in blocks:
            min_x = bx_start - 1
            max_x = bx_end
            min_y = by_start - 1
            max_y = by_end

            for pos in self.model.waste.bins.keys():
                x, y = pos
                if min_x <= x <= max_x and min_y <= y <= max_y:
                    assigned.add(pos)

        return sorted(assigned)

    def _containers_for_building_column(self, target_col: int) -> list[tuple[int, int]]:
        """
        Return containers close to one building column.
        """
        blocks = self._blocks_for_column(target_col)

        if not blocks:
            return list(self.model.waste.containers.keys())

        min_x = min(b[2] for b in blocks) - 10
        max_x = max(b[3] for b in blocks) + 10

        assigned = []
        for pos in self.model.waste.containers.keys():
            x, y = pos
            if min_x <= x <= max_x:
                assigned.append(pos)

        if not assigned:
            assigned = list(self.model.waste.containers.keys())

        return assigned

    def spawn_bin_transporters_by_building_column(self, capacity: int = 10) -> None:
        """
        Spawn one BinTransporterAgent per building column.
        Each transporter loops around the buildings of its column.
        """
        from agents.BinTransporterAgent import BinTransporterAgent

        for col in range(NUM_BLOCKS):
            patrol_path = self._build_building_column_patrol_path(col)

            if not patrol_path:
                print(f"No patrol path for transporter column {col}")
                continue

            assigned_bins = self._bins_for_building_column(col)
            assigned_containers = self._containers_for_building_column(col)

            start = patrol_path[0]

            agent = BinTransporterAgent(
                model=self.model,
                start_pos=start,
                patrol_path=patrol_path,
                assigned_bins=assigned_bins,
                assigned_containers=assigned_containers,
                capacity=capacity,
            )

            agent.transporter_sector = f"building_col_{col}"

            self.model.grid.place_agent(agent, start)

            #print(f"Bin transporter spawned for building column {col}")
            #print("Start:", start)
            #print("Assigned bins:", len(assigned_bins))
            #print("Assigned containers:", len(assigned_containers))
            #print("Patrol length:", len(patrol_path))


    # ------------------------------------------------------------------
    # Container transporter
    # ------------------------------------------------------------------

    def _ordered_container_positions_from_bottom_left(self) -> list[tuple[int, int]]:
        """
        Return all container positions ordered so that the patrol starts
        at the bottom-left container, then continues through the others.
        """
        containers = list(self.model.waste.containers.keys())
        if not containers:
            return []

        # bottom-left = smallest x, then smallest y
        start = min(containers, key=lambda p: (p[0], p[1]))

        remaining = [c for c in containers if c != start]

        # simple nearest-neighbor ordering from the chosen start
        ordered = [start]
        current = start

        while remaining:
            nxt = min(
                remaining,
                key=lambda p: abs(p[0] - current[0]) + abs(p[1] - current[1])
            )
            ordered.append(nxt)
            remaining.remove(nxt)
            current = nxt

        return ordered

    def _bottom_left_container(self) -> tuple[int, int] | None:
        """
        Return the bottom-left container position.
        """
        containers = list(self.model.waste.containers.keys())
        if not containers:
            return None
        return min(containers, key=lambda p: (p[0], p[1]))

    def spawn_container_transporter_simple(self, capacity: int = 30) -> None:
        """
        Spawn one transporter that moves from container to container.
        It starts at the bottom-left container.
        """
        from agents.ContainerTransporterAgent import ContainerTransporterAgent

        patrol_path = self._ordered_container_positions_from_bottom_left()
        if not patrol_path:
            print("No containers found for ContainerTransporterAgent.")
            return

        start = patrol_path[0]
        disposal = self._nearest_disposal(start)

        if disposal is None:
            print("No disposal area found for ContainerTransporterAgent.")
            return

        agent = ContainerTransporterAgent(
            model=self.model,
            start_pos=start,
            patrol_path=patrol_path,
            assigned_containers=patrol_path,
            disposal_pos=disposal,
            capacity=capacity,
        )

        agent.transporter_type = "container_transporter"
        self.model.grid.place_agent(agent, start)

        #print("Container transporter spawned")
        #print("Start (bottom-left container):", start)
        #print("Disposal:", disposal)
        #print("Assigned containers:", len(patrol_path))

    
    # ------------------------------------------------------------------
    # Model citizens
    # ------------------------------------------------------------------

    def _random_free_walkable_position(self) -> tuple[int, int] | None:
        candidates = [
            (x, y)
            for x in range(self.model.grid.width)
            for y in range(self.model.grid.height)
            if self.model.is_walkable((x, y))
            and len(self.model.grid.get_cell_list_contents([(x, y)])) == 0
            and 1 <= x < self.model.grid.width - 1
            and 1 <= y < self.model.grid.height - 1
        ]

        if not candidates:
            return None

        return random.choice(candidates)


    def spawn_model_citizen(self, capacity: int = 3) -> None:
        from agents.ModelCitizenAgent import ModelCitizenAgent

        start = self._random_free_walkable_position()
        if start is None:
            print("No free walkable position found for ModelCitizenAgent.")
            return

        agent = ModelCitizenAgent(
            model=self.model,
            start_pos=start,
            capacity=capacity,
        )

        self.model.grid.place_agent(agent, start)
        print("Model citizen spawned at:", start, "type=", type(agent))


    def spawn_model_citizens(self, count: int = 1, capacity: int = 3) -> None:
        for _ in range(count):
            self.spawn_model_citizen(capacity=capacity)

    