"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description: Quick annotation library for the particle tracking plugin.
"""

import warnings
from math import sqrt
from typing import Callable, Tuple

import numpy as np
from skimage import morphology
from skimage.draw import circle_perimeter, disk
from skimage.exposure import rescale_intensity
from skimage.feature import blob_log


def quick_segment_2d(
    _image: np.ndarray,
    _label: np.ndarray,
    min_sigma: float = 1.0,
    max_sigma: float = 2.0,
    num_sigma: int = 10,
    threshold: float = 0.1,
    overlap: float = 0.5,
) -> np.ndarray:
    """
    Quick segmentation of the particles in the image using the Laplacian of Gaussian (LoG) method.

    Parameters
    ----------
    _image : np.ndarray
        The image in which the particles are detected.
    _label : np.ndarray
        The labels of the particles in the image.
    min_sigma : float
        The minimum standard deviation for the LoG filter.
    max_sigma : float
        The maximum standard deviation for the LoG filter.
    num_sigma : int
        The number of standard deviations to be used.
    threshold : float
        The threshold for the LoG filter.
    overlap : float
        The overlap between the particles.

    Returns
    -------
    np.ndarray
        The labels of the particles in the image.
    """
    if _image is None:
        warnings.warn("No image layer found")
        return

    if _label is None:
        warnings.warn("No label layer found")
        return

    image: np.ndarray = _image
    label: np.ndarray = _label

    blobs_log = _quick_log(
        image,
        min_sigma=min_sigma,
        max_sigma=max_sigma,
        num_sigma=num_sigma,
        threshold=threshold,
        overlap=overlap,
    )
    label = _draw_points(label, blobs_log, fill_value=2, outline_value=1)
    label[label == 0] = 1  # set background to 1
    return label


def _draw_points(
    image: np.ndarray,
    points: np.ndarray,
    radius: int = 1,
    fill_value: int = 255,
    outline_value: int = 0,
) -> np.ndarray:
    """
    Draw the points on the image.

    Parameters
    ----------
    image : np.ndarray
        The image on which the points are to be drawn.
    points : np.ndarray
        The points to be drawn.
    radius : int
        The radius of the points.
    fill_value : int
        The fill value of the points.
    outline_value : int
        The outline value of the points.

    Returns
    -------
    np.ndarray
        The image with the points drawn.
    """

    def map_bound(limit: int) -> Callable[[int], int]:
        def fun(val: int) -> int:
            if val >= limit:
                val = limit - 1
            elif val < 0:
                val = 0
            return val

        return fun

    for y, x, r in points:
        _radius = r * sqrt(2)
        rr, cc = disk((y, x), radius=_radius, shape=image.shape)
        rr = np.array(list(map(map_bound(image.shape[0]), rr)), dtype="uint16")
        cc = np.array(list(map(map_bound(image.shape[1]), cc)), dtype="uint16")
        image[rr, cc] = fill_value
        if outline_value > 0:
            o_rr, o_cc = circle_perimeter(
                int(y), int(x), radius=int(np.ceil(_radius)), shape=image.shape
            )
            image[o_rr, o_cc] = outline_value

    return image


def remove_small_objects(
    img: np.ndarray, min_size: int = 10, connectivity: int = 2
) -> np.ndarray:
    # TODO: check if this is the correct way to remove small objects
    # not used in the current implementation
    binary = np.array(img > 0)
    binary = binary.astype(np.bool_)
    bim = morphology.binary_dilation(
        binary, footprint=np.ones((2, 2))
    )  # min_size=min_size, connectivity=connectivity
    bim = morphology.binary_opening(bim)
    ret = np.array(bim, dtype=np.uint8)
    return ret


def _quick_log(
    image: np.ndarray,
    min_sigma: float = 1.0,
    max_sigma: float = 2.0,
    num_sigma: int = 10,
    threshold: float = 0.1,
    overlap: float = 0.5,
) -> np.ndarray:
    """
    Quick detection of the particles in the image using the Laplacian of Gaussian (LoG) method.

    Parameters
    ----------
    image : np.ndarray
        The image in which the particles are detected.
    min_sigma : float
        The minimum standard deviation for the LoG filter.
    max_sigma : float
        The maximum standard deviation for the LoG filter.
    num_sigma : int
        The number of standard deviations to be used.
    threshold : float
        The threshold for the LoG filter.
    overlap : float
        The overlap between the particles.

    Returns
    -------
    np.ndarray
        The detected particles.
    """
    im_range: Tuple[float, float] = np.min(image), np.max(image)
    image = rescale_intensity(image, in_range=im_range, out_range=(0, 1))
    blobs_log = blob_log(
        image,
        min_sigma=min_sigma,
        max_sigma=max_sigma,
        num_sigma=num_sigma,
        threshold=threshold,
        overlap=overlap,
    )
    return blobs_log
