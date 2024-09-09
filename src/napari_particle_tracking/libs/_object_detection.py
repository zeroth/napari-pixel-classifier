"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description: This is the object detection module for the particle tracking plugin.
"""

import warnings
from typing import List

import numpy as np
import pandas as pd
from skimage import measure
from tqdm import tqdm

_defatul_properties = [
    "label",
    "area",
    "centroid",
    "mean_intensity",
    "max_intensity",
    "min_intensity",
    "bbox",
    "equivalent_diameter",
    "perimeter",
    "solidity",
]


def get_frame_regions_properties(
    frame_number: int,
    image: np.ndarray,
    labels: np.ndarray,
    properties: List[str] = None,
) -> pd.DataFrame:
    """
    Get the properties of the regions in the image.

    Parameters
    ----------
    frame_number : int
        The frame number.
    image : np.ndarray
        The image.
    labels : np.ndarray
        The labeled mask of the regions in the image.
    properties : List[str], optional
        The properties to be calculated.

    Returns
    -------
    pd.DataFrame
        The properties of the regions in the image.

    Note: Use measure.label to get the labels of the regions.
    """
    if image.ndim > 2:
        warnings.warn("Only 2D images are supported.")
        return

    if labels.ndim > 2:
        warnings.warn("Only 2D labels are supported.")
        return

    regions = measure.regionprops_table(
        labels, intensity_image=image, properties=properties
    )

    result = pd.DataFrame(regions)
    result["radius"] = np.sqrt(result["area"] / np.pi)

    if "centroid-2" in result.columns:
        result.rename(
            columns={"centroid-0": "z", "centroid-1": "y", "centroid-2": "x"},
            inplace=True,
        )
    else:
        result.rename(
            columns={"centroid-0": "y", "centroid-1": "x"}, inplace=True
        )

    result["frame"] = frame_number
    # reordering the columns to have the frame number as the first column
    cols = result.columns.tolist()
    cols = [cols[-1], *cols[:-1]]
    result = result[cols]
    return result


def get_timeseries_regions_properties(
    images: np.ndarray, masks: np.ndarray, properties: List[str] = None, progress = tqdm
) -> pd.DataFrame:
    # get the regions properties for the entire timeseries using the get_frame_regions_properties
    """
    Get the properties of the regions in the timeseries.

    Parameters
    ----------
    images : np.ndarray
        The image.
    masks : np.ndarray
        The binary mask of the regions in the image.
    properties : List[str], optional
        The properties to be calculated.

    Returns
    -------
    pd.DataFrame
        The properties of the regions in the timeseries.

    """
    _properties = properties if properties is not None else _defatul_properties

    if images.ndim == 2:
        images = np.expand_dims(images, axis=0)
    if masks.ndim == 2:
        masks = np.expand_dims(masks, axis=0)

    for i, (im, lab) in enumerate(progress(zip(images, masks))):
        _labels = measure.label(lab)
        if i == 0:
            result = get_frame_regions_properties(
                i, im, _labels, properties=_properties
            )
        else:
            result = pd.concat(
                [
                    result,
                    get_frame_regions_properties(
                        i, im, _labels, properties=_properties
                    ),
                ]
            )

    return result


class ObjectDetection:
    def __init__(self, image: np.ndarray, labels: np.ndarray):
        self.image = image
        self.labels = labels
        self.objects = None

    def detect_objects(self, properties: List[str] = None, progress=tqdm) -> pd.DataFrame:
        """
        Get the objects in the image.

        Parameters
        ----------
        properties : List[str], optional
            The properties to be calculated.

        Returns
        -------
        pd.DataFrame
            The properties of the objects in the image.
        """
        self.objects = get_timeseries_regions_properties(
            self.image, self.labels, properties=properties, progress=progress
        )
        return self.objects

    def get_objects_in_frame(
        self, frame_number: int, properties: List[str] = None
    ) -> pd.DataFrame:
        """
        Get the objects in the frame.

        Parameters
        ----------
        frame_number : int
            The frame number.
        properties : List[str], optional
            The properties to be calculated.

        Returns
        -------
        pd.DataFrame
            The properties of the objects in the frame.
        """

        properties = _defatul_properties if properties is None else properties

        if self.objects is None:
            self.get_objects(properties=properties)
        return self.objects[self.objects["frame"] == frame_number]

    def get_columns(self) -> List[str]:
        """
        Get the columns of the objects.

        Returns
        -------
        List[str]
            The columns of the objects.
        """
        return self.objects.columns.tolist()

    def to_numpy(self) -> np.ndarray:
        """
        Convert the objects to numpy.

        Returns
        -------
        np.ndarray
            The objects in numpy format.
        """
        return self.objects.to_numpy()

    def to_dict(self) -> dict:
        """
        Convert the objects to dictionary.

        Returns
        -------
        dict
            The objects in dictionary format.
        """
        return self.objects.to_dict()

    def to_csv(self, path: str) -> None:
        """
        Save the objects to a csv file.

        Parameters
        ----------
        path : str
            The path to save the csv file.
        """
        self.objects.to_csv(path, index=False)
