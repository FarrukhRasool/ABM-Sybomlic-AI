# model/waste/Bin.py

from constants import *

class Bin:
    """
    Represents a physical waste bin in the city.

    Main role:
        - Store waste deposited by agents
        - Keep track of current fill level
        - Report whether it is empty, full, or partially filled
    """

    # ==================================================================
    # Initialization
    # ==================================================================

    def __init__(self, pos: tuple, capacity: int = BIN_CAPACITY):
        self.pos      = pos
        self.capacity = capacity
        self._level   = 0
        self.is_active = True   # False if broken/removed infrastucture


    # ==================================================================
    # Read-only properties / queries
    # ==================================================================

    @property
    def level(self) -> int:
        """
        Return the current waste level of the bin.
        """
        return self._level

    @property
    def is_full(self) -> bool:
        """
        Return whether the bin has reached or exceeded its capacity.
        """
        return self._level >= self.capacity

    @property
    def is_empty(self) -> bool:
        """
        Return whether the bin currently contains no waste.
        """
        return self._level == 0

    @property
    def fill_ratio(self) -> float:
        """
        Return the fill ratio of the bin.
        0.0 = empty, 1.0 = full.
        """
        return self._level / self.capacity

    @property
    def available_space(self) -> int:
        """
        Return the remaining storage capacity of the bin.
        """
        return self.capacity - self._level


    # ==================================================================
    # State-changing operations
    # ==================================================================

    def deposit(self, amount: int) -> int:
        """
        Add waste to bin.
        Returns overflow — amount that didn't fit.
        """
        deposited   = min(amount, self.available_space)
        self._level += deposited
        return amount - deposited  # overflow

    def empty(self) -> int:
        """
        Empty the bin. Returns amount collected.
        """
        collected  = self._level
        self._level = 0
        return collected

    def __repr__(self):
        """
        Return a readable string representation of the bin.
        """
        return f"Bin(pos={self.pos}, {self._level}/{self.capacity})"