# model/waste/Bin.py

from constants import *

class Bin:
    """
    Represents a physical waste bin in the city.

    Real-world analogy:
        A street-side waste bin with a sensor that
        reports its fill level to the central system.
    """

    def __init__(self, pos: tuple, capacity: int = BIN_CAPACITY):
        self.pos      = pos
        self.capacity = capacity
        self._level   = 0
        self.is_active = True   # False if broken/removed

    # ------------------------------------------------------------------ #
    # Queries                                                              #
    # ------------------------------------------------------------------ #

    @property
    def level(self) -> int:
        return self._level

    @property
    def is_full(self) -> bool:
        return self._level >= self.capacity

    @property
    def is_empty(self) -> bool:
        return self._level == 0

    @property
    def fill_ratio(self) -> float:
        """0.0 = empty, 1.0 = full."""
        return self._level / self.capacity

    @property
    def available_space(self) -> int:
        return self.capacity - self._level

    # ------------------------------------------------------------------ #
    # Operations                                                           #
    # ------------------------------------------------------------------ #

    def deposit(self, amount: int) -> int:
        """
        Add waste to bin.
        Returns overflow — amount that didn't fit.
        """
        deposited   = min(amount, self.available_space)
        self._level += deposited
        return amount - deposited  # overflow

    def empty(self) -> int:
        """Empty the bin. Returns amount collected."""
        collected  = self._level
        self._level = 0
        return collected

    def __repr__(self):
        return f"Bin(pos={self.pos}, {self._level}/{self.capacity})"