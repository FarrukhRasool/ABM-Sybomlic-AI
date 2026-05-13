import matplotlib.pyplot as plt
import numpy as np

from model.city_model import CityModel

COLOR_MAP = {
    "road": [0.5, 0.5, 0.5],        # gray
    "sidewalk": [0.9, 0.9, 0.9],    # light gray
    "building": [0.0, 0.0, 0.0],    # black
    "attractive": [1.0, 0.8, 0.0],  # yellow
    "bin": [0.0, 0.6, 0.0],         # green
    "container": [0.0, 0.0, 1.0],   # blue
    "disposal": [1.0, 0.0, 0.0],    # red
}

model = CityModel()
width, height = model.grid.width, model.grid.height

image = np.zeros((height, width, 3))

for x in range(width):
    for y in range(height):
        cell_type = model.get_cell_type((x, y))
        image[height - y - 1, x] = COLOR_MAP[cell_type]

plt.figure(figsize=(8, 8))
plt.imshow(image)
plt.title("City Layout – Waste in the City")
plt.axis("off")
plt.show()