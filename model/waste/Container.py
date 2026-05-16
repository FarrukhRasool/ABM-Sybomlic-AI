# model/waste/Container.py

from constants import *

class Container:
    """
    Represents a large waste container in the city.

    Real-world analogy:
        A large communal waste container that collects
        from multiple bins. Emptied by transporter trucks.
    """

    def __init__(self, pos: tuple, capacity: int = CONTAINER_CAPACITY):
        self.pos      = pos
        self.capacity = capacity
        self._level   = 0
        self.is_active = True

        # Track which bins feed into this container (optional)
        self.assigned_bins: list = []

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
        return self._level / self.capacity

    @property
    def available_space(self) -> int:
        return self.capacity - self._level

    # ------------------------------------------------------------------ #
    # Operations                                                           #
    # ------------------------------------------------------------------ #

    def deposit(self, amount: int) -> int:
        """
        Add waste to container.
        Returns overflow.
        """
        deposited   = min(amount, self.available_space)
        self._level += deposited
        return amount - deposited

    def empty(self) -> int:
        """Empty the container. Returns amount collected."""
        collected   = self._level
        self._level = 0
        return collected

    def assign_bin(self, bin_obj) -> None:
        """Assign a bin to this container's collection zone."""
        if bin_obj not in self.assigned_bins:
            self.assigned_bins.append(bin_obj)

    def __repr__(self):
        return f"Container(pos={self.pos}, {self._level}/{self.capacity})"