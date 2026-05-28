# model/planning/SectorPlanner.py

from constants import *

class SectorPlanner:
    """
    Analyze the city structure and extract useful spatial sectors:
    streets, park sectors, building columns, bins, containers, etc.
    """

    # ==================================================================
    # Initialization 
    # ==================================================================
    def __init__(self, model):
        self.model = model

    
    # ==================================================================
    # Street cleaners - vertical streets
    # ==================================================================
    def _find_vertical_street_groups(self) -> list[list[int]]:
        """
        Detect vertical streets as groups of consecutive x-columns.

        A column is considered part of a vertical street if it contains
        enough ROAD cells.
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
    

    # ==================================================================
    # Street cleaners - horizontal streets
    # =================================================================     
    def _find_horizontal_street_groups(self) -> list[list[int]]:
        """
        Detect horizontal streets as groups of consecutive y-rows.

        A row is considered part of a horizontal street if it contains
        enough ROAD cells.
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
    
    # ==================================================================
    # Park detection helpers
    # ==================================================================
    
    def _find_park_vertical_columns(self) -> list[int]:
        """
        Return columns that belong to the vertical branch of the tourist area.

        Detection rule:
            A column is considered part of the tourist band if it contains
            enough ATTRACTIVE cells.
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
        Return rows that belong to the horizontal branch of the tourist area.

        Detection rule:
            A row is considered part of the tourist band if it contains
            enough ATTRACTIVE cells.
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
    

    # ==================================================================
    # Park cleaners - five-sector decomposition
    # ==================================================================

    def _get_attractive_cells(self) -> list[tuple[int, int]]:
        """
        Return all ATTRACTIVE cells of the city.
        """
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
    

    # ==================================================================
    # Bin transporters - building-column decomposition
    # ==================================================================

    def _get_building_blocks(self) -> list[tuple[int, int, int, int, int, int]]:
        """
        Return all building blocks as:
        (col_index, row_index, bx_start, bx_end, by_start, by_end)

        Important:
            Park blocks are excluded because they do not belong to the
            regular building sectors.
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
        Return all building blocks belonging to one logical building column.

        Sorting rule:
            blocks are sorted from top to bottom.
        """
        blocks = [b for b in self._get_building_blocks() if b[0] == target_col]
        return sorted(blocks, key=lambda b: b[5], reverse=True)
    
    def _bins_for_building_column(self, target_col: int) -> list[tuple[int, int]]:
        """
        Return bins associated with one building column.

        Rule:
            A bin is assigned to the column if it lies on or around one of
            the buildings in that column.
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
        Return containers associated with one building column.

        Rule:
            Containers are selected by horizontal proximity to that column.

        Fallback:
            If none are found nearby, all containers are returned.
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
    
    # ==================================================================
    # Container transporter
    # ==================================================================
    def _ordered_container_positions_from_bottom_left(self) -> list[tuple[int, int]]:
        """
        Return all container positions ordered as a patrol route.

        Ordering strategy:
            1. Start from the bottom-left container
            2. Repeatedly choose the nearest unvisited container
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