import cv2
import numpy as np


def is_handwritten(image_path):

    img = cv2.imread(image_path)

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    edges = cv2.Canny(
        gray,
        50,
        150
    )

    edge_density = (
        np.sum(edges > 0)
        / edges.size
    )

    return edge_density > 0.12