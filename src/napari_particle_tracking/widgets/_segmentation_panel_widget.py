"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description: Segmentation panel widget for the particle tracking plugin.
"""

from typing import TYPE_CHECKING

from qtpy.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ._base_widget import BaseWidget
from ._napari_layers_widget import NPLayersWidget
from ._pixel_classifier_widget import PixelClassifierWidget
from ._quick_annotation_widget import QuickAnnotationWidget

if TYPE_CHECKING:
    import napari


class SegmentationPanelWidget(BaseWidget):
    """
    Segmentation Panel Widget. This is the main widget for the segmentation section.

    Parameters
    ----------
    viewer: napari.viewer.Viewer
        Napari Viewer instance
    parent: QWidget
        Parent widget for the widget
    """

    def __init__(
        self,
        viewer: "napari.viewer.Viewer",
        nplayers_widget: NPLayersWidget,
        parent: QWidget = None,
    ):
        super().__init__(viewer, parent)
        self.setLayout(QVBoxLayout())

        self._nplayers_widget: NPLayersWidget = nplayers_widget

        self.layout().addWidget(QLabel("Quick Annotation"))
        self._quick_annotation_widget: QuickAnnotationWidget = (
            QuickAnnotationWidget(viewer, self._nplayers_widget)
        )
        self.layout().addWidget(self._quick_annotation_widget)

        self.layout().addWidget(QLabel("Pixel Classifier"))
        self._pixel_classifier_widget: PixelClassifierWidget = (
            PixelClassifierWidget(viewer, self._nplayers_widget)
        )
        self.layout().addWidget(self._pixel_classifier_widget)
        self.layout().addStretch()
