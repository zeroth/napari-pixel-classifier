"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description: Quick annotation widget helps in labeling the particles in the current displayed frame.
"""

import warnings
from typing import TYPE_CHECKING

import numpy as np
from qtpy.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QPushButton,
    QSpinBox,
    QWidget,
)

from napari_particle_tracking.libs import quick_segment_2d

from ._base_widget import BaseWidget
from ._napari_layers_widget import NPLayersWidget

if TYPE_CHECKING:
    import napari


class QuickAnnotationWidget(BaseWidget):
    """
    Quick Annotation Widget. This widget helps in labeling the particles in the current displayed frame.

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
    ):
        super().__init__(viewer, parent)
        self.setLayout(QFormLayout())

        self._layers_widget = layers_widget

        self._min_sigma = QDoubleSpinBox()
        self._min_sigma.setRange(0, 100)
        self._min_sigma.setValue(1)
        self.layout().addRow("Min Sigma", self._min_sigma)

        self._max_sigma = QDoubleSpinBox()
        self._max_sigma.setRange(0, 100)
        self._max_sigma.setValue(10)
        self.layout().addRow("Max Sigma", self._max_sigma)

        self._number_of_sigma = QSpinBox()
        self._number_of_sigma.setRange(1, 100)
        self._number_of_sigma.setValue(10)
        self.layout().addRow("Number of Sigma", self._number_of_sigma)

        self._threshold = QDoubleSpinBox()
        self._threshold.setRange(0, 1)
        self._threshold.setValue(0.01)
        self.layout().addRow("Threshold", self._threshold)

        self._overlap = QDoubleSpinBox()
        self._overlap.setRange(0, 1)
        self._overlap.setValue(0.5)
        self.layout().addRow("Overlap", self._overlap)

        self._verwrite = QCheckBox()
        self._verwrite.setChecked(False)
        self.layout().addRow("Overwrite", self._verwrite)

        self._quick_annotate_button = QPushButton("Quick Annotate")
        self._quick_annotate_button.clicked.connect(self._quick_annotate)
        self.layout().addRow(self._quick_annotate_button)

    def _quick_annotate(self):
        # collect the values from the widgets
        min_sigma: float = self._min_sigma.value()
        max_sigma: float = self._max_sigma.value()
        number_of_sigma: int = self._number_of_sigma.value()
        threshold: float = self._threshold.value()
        overlap: float = self._overlap.value()
        overwrite: bool = self._verwrite.isChecked()

        # get the selected layers
        selected_layer = self._layers_widget.get_selected_layers()
        if selected_layer is None:
            return
        # print(selected_layer)
        _image_layer = selected_layer.get("Image", None)
        _labels_layer = selected_layer.get("Labels", None)
        if _image_layer is None:
            warnings.warn("Please select an Image and Labels layer.")
            return

        if _image_layer.data is None:
            warnings.warn("Image layer is empty.")
            return

        if _labels_layer is None:
            _labels_layer_name = f"Annotation_{_image_layer.name }"
            _labels_layer = self.viewer.add_labels(
                np.zeros(_image_layer.data.shape, dtype=np.uint8),
                name=_labels_layer_name,
            )

        # get the current frame
        image = _image_layer.data[self.viewer.dims.current_step[0]]
        label = _labels_layer.data[self.viewer.dims.current_step[0]]

        if overwrite:
            label = np.zeros_like(label)

        # get the segmentation
        current_segmentation: np.ndarray = quick_segment_2d(
            image,
            label,
            min_sigma,
            max_sigma,
            number_of_sigma,
            threshold,
            overlap,
        )

        # add the segmentation to the viewer
        _labels_layer.data[self.viewer.dims.current_step[0]] = (
            current_segmentation
        )
        _labels_layer.refresh()
