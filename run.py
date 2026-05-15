# run.py — manual smoke test for the current sub-step.

from collections import Counter

from model.city_model import CityModel
from model.constants import GRID_WIDTH, GRID_HEIGHT


def main():
    model = CityModel()

    # Count every cell type in the semantic map.
    counts = Counter(
        model.get_cell_type((x, y))
        for x in range(GRID_WIDTH)
        for y in range(GRID_HEIGHT)
    )

    print("City model initialized.")
    print(f"Grid size: {GRID_WIDTH} x {GRID_HEIGHT}")
    print("Cell counts:", dict(counts))


if __name__ == "__main__":
    main()
