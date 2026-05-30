# model/waste/Container.py

from constants import *

class Container:
    """
    Represents a large waste container in the city.

    Main role:
        - Store larger amounts of waste than normal bins
        - Receive waste from transport agents
        - Serve as an intermediate storage layer before disposal
    """


    # ==================================================================
    # Initialization
    # ==================================================================
    def __init__(self, pos: tuple, capacity: int = CONTAINER_CAPACITY):
        self.pos      = pos
        self.capacity = capacity
        self._level   = 0
        self.is_active = True # False if broken/removed infrastucture

        # Track which bins feed into this container (optional)
        self.assigned_bins: list = []


    # ==================================================================
    # Read-only properties / queries
    # ==================================================================
    @property
    def level(self) -> int:
        """
        Return the current waste level of the container.
        """
        return self._level

    @property
    def is_full(self) -> bool:
        """
        Return whether the container has reached or exceeded its capacity.
        """
        return self._level >= self.capacity

    @property
    def is_empty(self) -> bool:
        """
        Return whether the container currently contains no waste.
        """
        return self._level == 0

    @property
    def fill_ratio(self) -> float:
        """
        Return the fill ratio of the container.
        0.0 = empty, 1.0 = full.
        """
        return self._level / self.capacity

    @property
    def available_space(self) -> int:
        """
        Return the remaining storage capacity of the container.
        """
        return self.capacity - self._level

   # ==================================================================
    # State-changing operations
    # ==================================================================

    def deposit(self, amount: int) -> int:
        """
        Add waste to container.
        Returns overflow.
        """
        deposited   = min(amount, self.available_space)
        self._level += deposited
        return amount - deposited

    def empty(self) -> int:
        """
        Empty the container. Returns amount collected.
        """
        collected   = self._level
        self._level = 0
        return collected

    def assign_bin(self, bin_obj) -> None:
        """
        Assign a bin to this container's collection zone.
        """
        if bin_obj not in self.assigned_bins:
            self.assigned_bins.append(bin_obj)

    def __repr__(self):
        """
        Return a readable string representation of the bin.
        """
        return f"Container(pos={self.pos}, {self._level}/{self.capacity})"