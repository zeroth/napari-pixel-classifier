import inspect
from typing import List, Optional, Tuple

import numpy as np
import skimage.filters as sf
from xgboost import XGBClassifier


def apply_feature(
    image: np.ndarray, features: str, numarical_params: Optional[float]
) -> np.ndarray:
    """
    Apply the feature to the image.
    Parameters
    ----------
    image : np.ndarray
        The image.
    features : str
        The feature to be applied to the image.
    numarical_params : float
        The numerical parameter for the feature.

    Returns
    -------
    np.ndarray
        The image with the feature applied.
    """
    if hasattr(sf, features):
        f = getattr(sf, features)
        sig = inspect.signature(f)
        if len(sig.parameters.keys()) > 1 and "sigma" in sig.parameters:
            return getattr(sf, features)(image, numarical_params)
        return getattr(sf, features)(image)

    if "_of_" in features:
        features = features.split("_of_")
        image = apply_feature(image, features[1], numarical_params)
        image = apply_feature(image, features[0], numarical_params)
        return image

    return image


def encode_ground_truth(ground_truth: np.ndarray) -> np.ndarray:
    """
    Encode the ground truth to 0-based indices.
    Parameters
    ----------
    ground_truth : np.ndarray (1D)
        The ground truth.(1-based indices)

    Returns
    -------
    np.ndarray
        The ground truth with 0-based indices.
    """
    uniques = np.unique(ground_truth)
    for i, u in enumerate(uniques):
        ground_truth[ground_truth == u] = i
    return ground_truth


def apply_features(image: np.ndarray, features: str) -> List[np.ndarray]:
    """
    Apply the features to the image.
    Parameters
    ----------
    image : np.ndarray
        The image.
    features : str
        The features to be applied to the image.

    Returns
    -------
    List[np.ndarray]
        The list of images with the features applied.
    """
    features_stack = []
    for feature in features.split(" "):
        feature_name = feature.split("=")[0]
        numarical_params = (
            float(feature.split("=")[1]) if "=" in feature else None
        )
        _image = apply_feature(image, feature_name, numarical_params)
        features_stack.append(_image)
    return features_stack


def generate_featured_stack(
    features: str,
    images: np.ndarray,
    ground_truth: Optional[np.ndarray] = None,
) -> Tuple[List[np.ndarray], Optional[np.ndarray]]:
    """
    Generate the featured stack of the images.
    Parameters
    ----------
    features : str
        The features to be applied to the images.
    images : np.ndarray
        The images.
    ground_truth : np.ndarray (optional)
        The ground truth.

    Returns
    -------
    tuple
        The list of featured images and the ground truth.
    """
    no_ground_truth_dim = len(images.shape)
    if ground_truth is not None:
        _ann_ind = np.argwhere(ground_truth >= 1)
        _ann_ind = np.unique(_ann_ind[:, 0])
        _ann_ind = _ann_ind.tolist()
        _annotation = ground_truth[_ann_ind]
        _images = images[_ann_ind]
        images = _images
        ground_truth = _annotation
        no_ground_truth_dim = len(ground_truth.shape)

    new_featured_images = []

    if (
        isinstance(images, list)
        or isinstance(images, tuple)
        or isinstance(images, set)
        or (
            hasattr(images, "shape")
            and len(images.shape) > no_ground_truth_dim
        )
    ):
        # print("Total images in gfs: ", len(images))
        for image in images:
            [
                new_featured_images.append(f)
                for f in apply_features(image, features)
            ]
    else:
        new_featured_images = apply_features(images, features)
    return new_featured_images, ground_truth


def to_numpy(
    featured_image_list: List[np.ndarray],
    ground_truth: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    """
    Convert the featured images and ground truth to numpy arrays which can be used for training.
    Parameters
    ----------
    featured_image_list : List[np.ndarray]
        The list of featured images.
    ground_truth : Optional[np.ndarray] (optional)
        The ground truth.

    Returns
    -------
    Tuple[np.ndarray, Optional[np.ndarray]]
        The numpy arrays of the featured images and the ground truth.
    """
    feature_stack = np.asarray(
        [np.asarray(f).ravel() for f in featured_image_list]
    ).T
    if ground_truth is None:
        return feature_stack, None
    else:
        # make the annotation 1-dimensional
        ground_truth_np = np.asarray(ground_truth).ravel()

        X = feature_stack
        y = ground_truth_np

        # remove all pixels from the feature and annotations which have not been annotated
        mask = y > 0

        X = X[mask]
        y = y[mask]

        y = encode_ground_truth(y)
        # y[y==1] = 0
        # y[y==2] = 1

        return X, y


class PixelClassifier:
    """
    A pixel classifier which uses XGBoost to classify the pixels.
    """

    def __init__(self, n_estimators: int = 100, max_depth: int = 2):
        """
        Initialize the pixel classifier.
        Parameters
        ----------
        n_estimators : int
            The number of estimators.
        max_depth : int
            The maximum depth of the tree.

        """
        self.features = "original gaussian=1 difference_of_gaussian=1 laplace_of_gaussian=1"
        self.X = None
        self.y = None
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.no_ground_truth_dim = 0

        self.clf = XGBClassifier(
            n_estimators=self.n_estimators, max_depth=self.max_depth
        )

    def train(
        self,
        images: np.ndarray,
        ground_truth: Optional[np.ndarray],
        features: Optional[str] = None,
    ):
        self.features = features if features is not None else self.features
        self.X, self.y = to_numpy(
            *generate_featured_stack(self.features, images, ground_truth)
        )
        self.clf.fit(self.X, self.y)

    def predict(self, images: np.ndarray) -> np.ndarray:
        return self.clf.predict(
            to_numpy(*generate_featured_stack(self.features, images))[0]
        )

    def score(
        self, images: np.ndarray, ground_truth: Optional[np.ndarray]
    ) -> float:
        return self.clf.score(
            to_numpy(*generate_featured_stack(self.features, images))[0]
        )

    def fit_predict(
        self, images: np.ndarray, ground_truth: Optional[np.ndarray]
    ) -> np.ndarray:
        self.train(images, ground_truth)
        return self.predict(images)


def test():
    import sys

    features = "original gaussian=1 difference_of_gaussian=1 laplace_of_gaussian=1 gaussian=0.5 difference_of_gaussian=0.5 laplace_of_gaussian=0.5 gaussian=0.3 difference_of_gaussian=0.3 laplace_of_gaussian=0.3"
    im = sys.argv[
        1
    ]  # tifffile.imread("D:\\Data\\Thomas_lab_pune\\Diffusion_Liposomes (TxRed)_50ms interval.tif")
    ground_truth = sys.argv[
        2
    ]  # tifffile.imread("D:\\Data\\Thomas_lab_pune\\Diffusion_Liposomes (TxRed)_50ms interval_annotation.tif")
    print("Total images: ", im.shape)
    features_images = generate_featured_stack(features, im)[0]
    print("Total features images: ", len(features_images))
    print("Total features: ", len(features.split(" ")))
    print("Feature image shape: ", features_images[0].shape)
    print(
        "numpy shape ",
        to_numpy(features_images, ground_truth=ground_truth)[0].shape,
    )


if __name__ == "__main__":
    test()
