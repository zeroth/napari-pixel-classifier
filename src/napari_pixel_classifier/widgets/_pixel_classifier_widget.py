"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description:  Pixel classifier widget for the particle tracking plugin.
"""

import warnings
from typing import TYPE_CHECKING, List, Union

import numpy as np
from napari.utils.progress import progress
from qtpy.QtCore import Signal, Qt
from qtpy.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QSlider,
)

from napari_pixel_classifier.libs import PixelClassifier

from ._base_widget import BaseWidget
from ._napari_layers_widget import NPLayersWidget
from skimage.measure import regionprops_table
import pandas as pd

from skimage.measure import label
from skimage.morphology import remove_small_objects, remove_small_holes

if TYPE_CHECKING:
    import napari
from napari.layers import Image, Labels


class _single_feature_widget(QWidget):
    feature_added = Signal(str)
    feature_removed = Signal(str)

    def __init__(
        self,
        feature_name: str,
        sigma_range: List[float],
        parent: QWidget = None,
    ) -> None:
        super().__init__(parent)
        self._feature_name: str = feature_name
        self._feature_range: List[float] = sigma_range

        self._layout: QHBoxLayout = QHBoxLayout()
        self.setLayout(self._layout)

        for value in self._feature_range:
            _check_box: QCheckBox = QCheckBox(str(value))
            _check_box.setChecked(False)
            self._layout.addWidget(_check_box)
            _check_box.stateChanged.connect(self._update_features)

    def _update_features(self, state: int) -> None:
        _current_checkbox: QCheckBox = self.sender()
        if _current_checkbox.isChecked():
            self.feature_added.emit(
                f"{self._feature_name}={_current_checkbox.text()}"
            )
        else:
            self.feature_removed.emit(
                f"{self._feature_name}={_current_checkbox.text()}"
            )


class FeatureSelectionWidget(QWidget):
    """
    Feature Selection Widget


    This class is the helper widget for the feature selection in the pixel classifier.

    Parameters
    ----------
    parent: QWidget
        Parent widget for the widget

    Methods
    -------
    get_features()
        Returns the selected features in the widget.
    """

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._default_features: str = (
            " original gaussian=1 difference_of_gaussian=1 laplace_of_gaussian=1 gaussian=0.5 difference_of_gaussian=0.5 laplace_of_gaussian=0.5 gaussian=0.3 difference_of_gaussian=0.3 laplace_of_gaussian=0.3 "
        )
        self._features: str = ""
        self._available_features: List[str] = [
            "gaussian",
            "difference_of_gaussian",
            "laplace_of_gaussian",
        ]
        self._available_features_short: List[str] = ["Gauss", "DoG", "LoG"]
        self._available_features_tooltips: List[str] = [
            "Gaussian",
            "Difference of Gaussian",
            "Laplace of Gaussian",
        ]

        self._feature_range: List[float] = [
            0.3,
            0.5,
            1,
            2,
            3,
            4,
            5,
            10,
            15,
            25,
        ]

        self._layout: QFormLayout = QFormLayout()
        self.setLayout(self._layout)

        for feature, short, tooltip in zip(
            self._available_features,
            self._available_features_short,
            self._available_features_tooltips,
        ):
            _widget: _single_feature_widget = _single_feature_widget(
                feature, self._feature_range
            )
            _widget.feature_added.connect(self._add_feature)
            _widget.feature_removed.connect(self._remove_feature)
            _widget.setToolTip(tooltip)
            self._layout.addRow(short, _widget)

        self._keep_original: QCheckBox = QCheckBox("Keep Original")
        self._keep_original.setChecked(True)
        self._features = " original "

        def _update_original(state: int) -> None:
            if self._keep_original.isChecked():
                self._add_feature("original")
            else:
                self._remove_feature("original")

        self._keep_original.stateChanged.connect(_update_original)

        self._layout.addRow(self._keep_original)

    def _add_feature(self, feature: str) -> None:
        self._features = self._features + " " + feature + " "
        # print("added: ", self._features)

    def _remove_feature(self, feature: str) -> None:
        self._features = (
            " "
            + (self._features.replace(" " + feature + " ", " ")).strip()
            + " "
        )
        # print("removed: ", self._features)

    def get_features(self) -> str:
        return (
            self._features if self._features != "" else self._default_features
        )


class PixelClassifierWidget(BaseWidget):
    """
    Pixel Classifier Widget

    This class is the main widget for the pixel classifier.

    Parameters
    ----------
    viewer: napari.viewer.Viewer
        Napari Viewer instance
    layers_widget: NPLayersWidget
        Napari Layers Widget instance
    parent: QWidget
        Parent widget for the widget
    """

    def __init__(
        self,
        viewer: "napari.viewer.Viewer",
        layers_widget: NPLayersWidget,
        parent: QWidget = None,
    ) -> None:
        super().__init__(viewer, parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self._features_selection_widget: FeatureSelectionWidget = (
            FeatureSelectionWidget()
        )
        self.layout().addWidget(self._features_selection_widget)
        self._btn: QPushButton = QPushButton("Train & Classify")

        _parametr_layout: QHBoxLayout = QHBoxLayout()
        _parametr_layout.addWidget(QLabel("No of Estimators/Trees"))
        self._n_estimators: QSpinBox = QSpinBox()
        self._n_estimators.setRange(1, 1000)
        self._n_estimators.setValue(10)
        _parametr_layout.addWidget(self._n_estimators)

        _parametr_layout.addWidget(QLabel("Max Depth"))
        self._max_depth: QSpinBox = QSpinBox()
        self._max_depth.setRange(1, 100)
        self._max_depth.setValue(2)
        _parametr_layout.addWidget(self._max_depth)

        self.layout().addLayout(_parametr_layout)

        self.layout().addWidget(self._btn)
        self._btn.clicked.connect(self._train_and_classify)
        self._layers_widget: NPLayersWidget = layers_widget

        # add slider for min size and max size
        _cleanup_layout: QHBoxLayout = QHBoxLayout()
        self._min_size: QSpinBox = QSpinBox()
        # self._min_size.setTracking(False)
        # self._min_size.setTickInterval(1)
        # self._min_size.setTickPosition(QSpinBox.TicksBelow)
        self._min_size.setRange(1, 100)
        self._min_size.setValue(4)
        _cleanup_layout.addWidget(QLabel("Min Size"))
        _cleanup_layout.addWidget(self._min_size)

        self._max_size: QSpinBox = QSpinBox()
        # self._max_size.setTracking(False)
        # self._max_size.setTickInterval(5)
        # self._max_size.setTickPosition(QSpinBox.TicksBelow)
        self._max_size.setRange(1, 100)
        self._max_size.setValue(100)
        _cleanup_layout.addWidget(QLabel("Max Size"))
        _cleanup_layout.addWidget(self._max_size)
        self.layout().addLayout(_cleanup_layout)
        self.layout().addStretch()

    def _train_and_classify(self) -> None:
        features: str = self._features_selection_widget.get_features()
        selected_layer: dict[str, Union[Image, Labels]] = (
            self._layers_widget.get_selected_layers()
        )

        # get the selected layers
        if selected_layer is None:
            return

        _image_layer: Image = selected_layer.get("Image")
        _labels_layer: Labels = selected_layer.get("Labels")
        if _image_layer is None:
            warnings.warn("Please select/add an Image layer.")
            return

        if _image_layer.data is None:
            warnings.warn("Image layer is empty.")
            return

        if _labels_layer is None:
            warnings.warn("Please select/add an Annotation layer.")
            return

        if _labels_layer.data is None:
            warnings.warn("Annotation layer is empty.")
            return

        images: np.ndarray = _image_layer.data
        ground_truth: np.ndarray = _labels_layer.data

        _n_etimators: int = self._n_estimators.value()
        _max_depth: int = self._max_depth.value()
        _classifier: PixelClassifier = PixelClassifier(
            n_estimators=_n_etimators, max_depth=_max_depth
        )
        _classifier.train(images, ground_truth, features=features)

        _prediction: np.ndarray = np.dstack(
            [
                _classifier.predict(im).reshape(im.shape)
                for im in progress(images, "Predicting")
            ]
        )
        if _prediction.ndim == 3:
            _prediction = _prediction.swapaxes(0, 2).swapaxes(1, 2)

        def _has_layer(name: str) -> bool:
            for layer in self.viewer.layers:
                if layer.name.strip() == name.strip():
                    return True
            return False

        _prediction_layer_name: str = f"Prediction_{_image_layer.name}"
        self._prediction_layer: Labels = (
            self.viewer.layers[_prediction_layer_name]
            if _has_layer(_prediction_layer_name) > 0
            else self.viewer.add_labels(
                np.zeros(images.shape, dtype=np.uint8),
                name=_prediction_layer_name,
            )
        )

        # clean up smaller objects
        # from skimage.morphology import remove_small_objects
        # _prediction = remove_small_objects(
        #     _prediction > 0, min_size=4
        # )
        self._prediction_layer.data = _prediction

        _predicted_labels_layer_name: str = f"Labels_{_image_layer.name}"
        self._predicted_labels_layer: Labels = (
            self.viewer.layers[_predicted_labels_layer_name]
            if _has_layer(_predicted_labels_layer_name) > 0
            else self.viewer.add_labels(
                np.zeros(images.shape, dtype=np.uint8),
                name=_predicted_labels_layer_name,
            )
        )

        _labels = label(_prediction > 0)
        self._predicted_labels_layer.data = _labels

        # measure min size and max size
        prop_table = regionprops_table(_labels, properties=['area', 'label'])
        prop_df = pd.DataFrame(prop_table)
        self._predicted_labels_layer.metadata['props'] = prop_df
        all_objects_size = prop_df['area']
        min_object_size = all_objects_size.min()
        max_object_size = all_objects_size.max()

        # set min size and max size to slider range
        self._min_size.setRange(int(min_object_size), int(max_object_size))
        self._min_size.setValue(int(min_object_size))
        self._max_size.setRange(int(min_object_size), int(max_object_size))
        self._max_size.setValue(int(max_object_size))
        self._min_size.valueChanged.connect(self._apply_object_cleanup)
        # self._max_size.valueChanged.connect(self._apply_object_cleanup)

    def _apply_object_cleanup(self):
        # _labeled_data = self._predicted_labels_layer.data
        # _label_df = self._predicted_labels_layer.metadata.get('props', None)
        # if _label_df is None:
        #     return
        # min_size = self._min_size.value()
        # max_size = self._max_size.value()
        # if min_size >= max_size:
        #     return
        
        # _new_labels = np.zeros(_labeled_data.shape, dtype=_labeled_data.dtype)

        # for prop in _label_df.itertuples():
        #     # 'area' is the size (pixel/voxel count)
        #     if prop.area >= min_size and prop.area <= max_size:
        #         # Reconstruct the object in the result mask
        #         _new_labels[_labeled_data == prop.label] = prop.label
        # self._predicted_labels_layer.data = _new_labels
        # self._prediction_layer.data = _new_labels > 0
        # self._predicted_labels_layer.metadata['props'] = _label_df
        min_size = self._min_size.value()
        _labels = label(self._prediction_layer.data)

        # remove small objects
        cleaned_labels = remove_small_objects(
            _labels, min_size=min_size
        )

        # # fill small holes
        # cleaned_labels = remove_small_holes(
        #     cleaned_labels, area_threshold=min_size
        # )

        self._predicted_labels_layer.data = cleaned_labels
        # self._prediction_layer.data = cleaned_labels > 0
        # self._predicted_labels_layer.metadata['props'] = _label_df
        self._predicted_labels_layer.refresh()
        # self._prediction_layer.refresh()