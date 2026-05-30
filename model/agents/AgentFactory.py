# model/factory/AgentFactory.py

import random
from constants import *
from agents.CleanerStreetAgent import CleanerStreetAgent
from agents.BinTransporterAgent import BinTransporterAgent
from agents.ContainerTransporterAgent import ContainerTransporterAgent
from agents.ModelCitizenAgent import ModelCitizenAgent
from agents.TouristAgent import TouristAgent
from agents.HumanAgent import HumanAgent
########################
from planning.PatrolPlanner import PatrolPlanner
from planning.SectorPlanner import SectorPlanner
##########################


class AgentFactory:
    """
    Factory responsible for creating and placing agents in the simulation.

    Main responsibilities:
        - Scan the city map for important positions
        - Spawn agents at valid positions
        - Assign initial patrol routes or task sectors when needed

    Real-world analogy:
        A city management office that decides where residents, tourists,
        cleaners, and transport workers start their activity.
    """

    # ==================================================================
    # Initialization and cached map locations
    # ==================================================================

    def __init__(self, model):
        self.model = model
        self._door_positions = self._find_doors()
        self._disposal_positions = self._find_disposal()

        #####
        self.sector_planner = SectorPlanner(model)
        self.patrol_planner = PatrolPlanner(model)
        #####

    
    # ==================================================================
    # Cached map locations
    # ==================================================================
    
    def _find_doors(self) -> list:
        """
        Scan grid and collect all door positions.
        """
        doors = []
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if self.model.get_cell_type((x, y)) == DOOR:
                    doors.append((x, y))
        return doors
    
    def _find_disposal(self):
        """
        Scan grid and collect all disposal area positions.
        """
        disposal = []
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if self.model.get_cell_type((x, y)) == DISPOSAL:
                    disposal.append((x, y))
        return disposal

    def _nearest_disposal(self, start: tuple):
        """
        Return the disposal area closest to the given position.
        """

        if not self._disposal_positions:
            return None

        return min(
            self._disposal_positions,
            key=lambda p: abs(p[0] - start[0]) + abs(p[1] - start[1])
        )


    # ==================================================================
    # Human agents
    # ==================================================================

    def spawn_human(self) -> None:
        """
        Spawn a HumanAgent at a random door heading to another random door.
        Start and destination must be different doors.
        """

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
        """
        Spawn multiple human agents.
        """
        for _ in range(count):
            self.spawn_human()

    
    # ==================================================================
    # Tourist agents
    # ==================================================================

    def spawn_tourist(self) -> None:
        """
        Spawn a tourist at a random park (attractive) cell.
        """
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
        """
        Spawn multiple tourist agents.
        """
        for _ in range(count):
            self.spawn_tourist()

    def respawn_tourists_if_needed(self, minimum: int = 1) -> None:
        """
        Maintain at least a minimum number of tourists in the model.
        Helps to keep tourist during the simulation (Tourist disappear after some time).
        """
        current = sum(1 for a in self.model.agents if isinstance(a, TouristAgent))
        if current < minimum:
            self.spawn_tourists(minimum - current)


    # ==================================================================
    # Street cleaners - vertical streets
    # ==================================================================

    def spawn_one_cleaner_per_vertical_street(self, capacity: int = 1) -> None:
        """
        Detect all vertical street groups and spawn one cleaner per street.

        Patrol strategy:
            - go downward on one lane
            - go upward on the opposite lane
        """
        street_groups = self.sector_planner._find_vertical_street_groups()

        for group in street_groups:
            patrol_path = self.patrol_planner._build_vertical_street_patrol_path(group)

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
                capacity=capacity,
            )
            agent.patrol_orientation = "vertical"

            self.model.grid.place_agent(agent, start)

            # ------------------------------------------------------------
            # Debug : Check the generation of vertical street cleaner setup
            # ------------------------------------------------------------
            print("Cleaner spawned on street:", group)
            print("Start:", start, "Disposal:", disposal)
            print("Patrol length:", len(patrol_path))
            print("===================================================", "\n")

    
    # ==================================================================
    # Street cleaners - horizontal streets
    # =================================================================    

    def spawn_one_cleaner_per_horizontal_street(self, capacity: int = 1) -> None:
        """
        Detect all horizontal streets and spawn one cleaner per street.

        Patrol strategy:
            - move right on the upper lane
            - move left on the lower lane
        """
        street_groups = self.sector_planner._find_horizontal_street_groups()

        for group in street_groups:
            patrol_path = self.patrol_planner._build_horizontal_street_patrol_path(group)

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
                capacity=capacity,
            )
            agent.patrol_orientation = "horizontal"

            self.model.grid.place_agent(agent, start)

            # ------------------------------------------------------------
            # Debug : Check the generation of horizontal street cleaner setup
            # ------------------------------------------------------------
            print("Horizontal cleaner spawned on street:", group)
            print("Start:", start, "Disposal:", disposal)
            print("Patrol length:", len(patrol_path))
            print("Horizontal street groups found:", street_groups)
            print("Horizontal patrol path sample:", patrol_path[:10], "...", patrol_path[-10:])
            print("===================================================", "\n")


    # ==================================================================
    # Park cleaners - five-sector decomposition
    # ==================================================================

    def spawn_park_cleaners_five_sectors(self, capacity: int = 5) -> None:
        """
         Spawn one CleanerParkAgent per park sector.

        Sectors:
            - center
            - north
            - south
            - west
            - east
        """
        from agents.CleanerParkAgent import CleanerParkAgent

        sectors = self.sector_planner._split_park_into_five_sectors()

        print("Park sectors detected:")
        for sector_name, cells in sectors.items():
            print(f"  - {sector_name}: {len(cells)} cells")

        for sector_name, cells in sectors.items():
            patrol_path = self.patrol_planner._build_park_sector_patrol_path(sector_name, cells)

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

            # ------------------------------------------------------------
            # Debug : Check the generation of park cleaner setup
            # ------------------------------------------------------------
            print(f"Park cleaner spawned: sector={sector_name}")
            print("Start:", start, "Disposal:", disposal)
            print("Patrol length:", len(patrol_path))
            print("===================================================", "\n")

    # ==================================================================
    # Bin transporters - building-column decomposition
    # ==================================================================

    def spawn_bin_transporters_by_building_column(self, capacity: int = 10) -> None:
        """
        Spawn one BinTransporterAgent per building column.

        Sector strategy:
            - one transporter per logical building column
            - each transporter receives:
                * a local patrol path
                * bins from that column
                * nearby containersSpawn one BinTransporterAgent per building column.
        Each transporter loops around the buildings of its column.
        """
        from agents.BinTransporterAgent import BinTransporterAgent

        for col in range(NUM_BLOCKS):
            blocks = self.sector_planner._blocks_for_column(col)
            patrol_path = self.patrol_planner._build_building_column_patrol_path(blocks)

            if not patrol_path:
                print(f"No patrol path for transporter column {col}")
                continue

            assigned_bins = self.sector_planner._bins_for_building_column(col)
            assigned_containers = self.sector_planner._containers_for_building_column(col)

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

            # ------------------------------------------------------------
            # Debug : Check the generation of bin transporter setup
            # ------------------------------------------------------------
            print(f"Bin transporter spawned for building column {col}")
            print("Start:", start)
            print("Assigned bins:", len(assigned_bins))
            print("Assigned containers:", len(assigned_containers))
            print("Patrol length:", len(patrol_path)), "\n"
            print("==================================================="), "\n"


    # ==================================================================
    # Container transporter
    # ==================================================================

    def spawn_container_transporter_simple(self, capacity: int = 30) -> None:
        """
        Spawn one ContainerTransporterAgent.

        Patrol logic:
            - start at the bottom-left container
            - follow the ordered container route
            - use the nearest disposal area as unloading target
        """
        from agents.ContainerTransporterAgent import ContainerTransporterAgent

        patrol_path = self.sector_planner._ordered_container_positions_from_bottom_left()
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

        # ------------------------------------------------------------
        # Debug : Check the generation of container transporter setup
        # ------------------------------------------------------------
        print("Container transporter spawned")
        print("Start (bottom-left container):", start)
        print("Disposal:", disposal)
        print("Assigned containers:", len(patrol_path))
        print("==================================================="), "\n"
    
    # ==================================================================
    # Model citizens
    # ==================================================================

    def _random_free_walkable_position(self) -> tuple[int, int] | None:
        """
        Return a random walkable position that is currently unoccupied.
        """
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
        """
        Spawn one ModelCitizenAgent at a random free walkable position.
        """
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

        # ------------------------------------------------------------
        # Debug : Check the generation of model citizen setup
        # ------------------------------------------------------------
        print("Model citizen spawned at:", start, "type=", type(agent))


    def spawn_model_citizens(self, count: int = 1, capacity: int = 3) -> None:
        """
        Spawn multiple model citizens.
        """
        for _ in range(count):
            self.spawn_model_citizen(capacity=capacity)

    