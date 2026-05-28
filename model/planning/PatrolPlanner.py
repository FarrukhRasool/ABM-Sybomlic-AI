# model/planning/PatrolPlanner.py

from constants import *

class PatrolPlanner:
    """
    Build patrol routes for cleaners and transporters.
    """

    # ==================================================================
    # Initialization 
    # ==================================================================
    def __init__(self, model):
        self.model = model


    # ==================================================================
    # Street cleaners - vertical streets
    # ==================================================================
    def _build_vertical_street_patrol_path(self, group: list[int]) -> list[tuple]:
        """
        Build a patrol path for one vertical street group.

        Strategy:
            - move downward on the left lane
            - move upward on the right lane

        Special case:
            If the street has width 1, the cleaner goes down and then back
            up on the same column.
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
    

    # ==================================================================
    # Street cleaners - horizontal streets
    # =================================================================  
    def _build_horizontal_street_patrol_path(self, group: list[int]) -> list[tuple]:
        """
        Build a patrol path for one horizontal street group.

        Strategy:
            - move right on the upper row
            - move left on the lower row
        """
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
    

    # ==================================================================
    # Park detection helpers
    # ==================================================================

    def _build_park_vertical_patrol_path(self, columns: list[int]) -> list[tuple]:
        """
        Build a serpentine patrol path through ATTRACTIVE cells
        for the vertical tourist-area sector.
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
        for the horizontal tourist-area sector.
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
    

    # ==================================================================
    # Park cleaners - five-sector decomposition
    # ==================================================================

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
    

    # ==================================================================
    # Bin transporters - building-column decomposition
    # ==================================================================

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
    
    def _build_building_column_patrol_path(
        self,
        blocks: list[tuple[int, int, int, int, int, int]]
    ) -> list[tuple[int, int]]:
        """
        Build a patrol path for one building column from a list of building blocks.
        """
        full_path = []

        for _, _, bx_start, bx_end, by_start, by_end in blocks:
            block_loop = self._build_loop_around_block(bx_start, bx_end, by_start, by_end)

            if not block_loop:
                continue

            full_path.extend(block_loop)

        return full_path