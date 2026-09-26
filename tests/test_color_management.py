"""v1.3.1: colour-managed image loading (utils.load_image)."""
import io
import os

import numpy as np
import pytest
from PIL import Image, ImageCms

from modules import utils

GENERIC_RGB = [
    "/System/Library/ColorSync/Profiles/Generic RGB Profile.icc",
    "/Library/ColorSync/Profiles/Generic RGB Profile.icc",
]


def _img(tmp_path, name, icc=None):
    rng = np.random.default_rng(0)
    a = rng.integers(0, 256, size=(40, 50, 3), dtype=np.uint8)
    p = tmp_path / name
    kw = {"icc_profile": icc} if icc else {}
    Image.fromarray(a).save(p, **kw)
    return p, a


def test_untagged_image_is_unchanged(tmp_path):
    p, a = _img(tmp_path, "plain.png")
    out = utils.load_image(str(p))
    assert np.array_equal(out, a)
    assert utils.LAST_LOAD_INFO["converted_to_srgb"] is False


def test_srgb_tagged_image_is_unchanged(tmp_path):
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    p, a = _img(tmp_path, "srgb.png", srgb)
    out = utils.load_image(str(p))
    assert np.array_equal(out, a)
    assert utils.LAST_LOAD_INFO["converted_to_srgb"] is False


def test_buffer_and_path_give_same_result(tmp_path):
    p, a = _img(tmp_path, "b.png")
    with open(p, "rb") as fh:
        buf = io.BytesIO(fh.read())
    assert np.array_equal(utils.load_image(buf), utils.load_image(str(p)))


def test_to_srgb_false_keeps_raw_values(tmp_path):
    icc = next((open(f, "rb").read() for f in GENERIC_RGB if os.path.exists(f)), None)
    if icc is None:
        pytest.skip("Generic RGB profile only available on macOS")
    p, a = _img(tmp_path, "gen.png", icc)
    assert np.array_equal(utils.load_image(str(p), to_srgb=False), a)


def test_generic_rgb_is_converted(tmp_path):
    icc = next((open(f, "rb").read() for f in GENERIC_RGB if os.path.exists(f)), None)
    if icc is None:
        pytest.skip("Generic RGB profile only available on macOS")
    p, a = _img(tmp_path, "gen.png", icc)
    out = utils.load_image(str(p))
    assert utils.LAST_LOAD_INFO["converted_to_srgb"] is True
    # Generic RGB (gamma 1.8) values map to lighter sRGB values in the mid-tones
    mid = (a > 60) & (a < 200)
    assert out[mid].astype(float).mean() > a[mid].astype(float).mean()
    # black and white stay black and white
    blk = Image.fromarray(np.zeros((4, 4, 3), np.uint8)); blk.save(tmp_path / "k.png", icc_profile=icc)
    assert utils.load_image(str(tmp_path / "k.png")).max() <= 1
