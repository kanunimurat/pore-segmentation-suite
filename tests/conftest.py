"""Shared fixtures for the Pore Segmentation Suite test suite."""
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def make_synthetic_stone(size=400, n_pores=40, r_min=4, r_max=12, seed=0,
                         background=(205, 180, 145), pore=(60, 50, 38),
                         noise_sd=4.0):
    """
    Synthetic 'travertine-like' surface: a light, slightly noisy background with
    dark circular pores of known position and size.

    Returns (img_rgb uint8, truth_mask bool). The truth mask is the exact
    ground truth against which segmentation output is scored.
    """
    rng = np.random.RandomState(seed)
    yy, xx = np.mgrid[0:size, 0:size]
    truth = np.zeros((size, size), dtype=bool)
    for _ in range(n_pores):
        r = rng.randint(r_min, r_max + 1)
        cy, cx = rng.randint(r + 2, size - r - 2, size=2)
        truth |= (yy - cy) ** 2 + (xx - cx) ** 2 <= r * r
    img = np.empty((size, size, 3), dtype=np.float64)
    img[:] = background
    img[truth] = pore
    img += rng.normal(0.0, noise_sd, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8), truth


@pytest.fixture(scope="session")
def synthetic_stone():
    return make_synthetic_stone()


def dice(a, b):
    a = a.astype(bool)
    b = b.astype(bool)
    s = a.sum() + b.sum()
    return 1.0 if s == 0 else 2.0 * np.logical_and(a, b).sum() / s
