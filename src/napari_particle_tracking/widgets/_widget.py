"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description:  Main widget for the particle tracking plugin.
"""

from typing import TYPE_CHECKING

from qtpy.QtWidgets import (
    QTabWidget,
    QVBoxLayout,
)

from ._base_widget import BaseWidget, create_wraper_widget
from ._napari_layers_widget import NPLayersWidget
from ._segmentation_panel_widget import SegmentationPanelWidget
from ._tracking_panel_widget import TrackingPanelWidget

if TYPE_CHECKING:
    import napari


class ParticleTrackingWidget(BaseWidget):
    """
    A widget for particle tracking in napari.
    Parameters:
    -----------
    viewer : napari.viewer.Viewer
        The napari viewer instance.
    Attributes:
    -----------
    _tab_widget : QTabWidget
        The tab widget for displaying different panels.
    _segmentation_widget : SegmentationPanelWidget
        The segmentation panel widget.
    _tracking_widget : TrackingPanelWidget
        The tracking panel widget.
    """

    def __init__(self, viewer: "napari.viewer.Viewer") -> None:
        super().__init__(viewer)
        self.setLayout(QVBoxLayout())
        self._nplayers_widget: NPLayersWidget = NPLayersWidget(viewer, self)
        self.layout().addWidget(self._nplayers_widget)
        self._tab_widget: QTabWidget = QTabWidget(self)
        self.layout().addWidget(self._tab_widget)
        self._segmentation_widget: SegmentationPanelWidget = (
            SegmentationPanelWidget(
                viewer, nplayers_widget=self._nplayers_widget
            )
        )
        self._tab_widget.addTab(self._segmentation_widget, "Segmentation")

        self._tracking_widget: TrackingPanelWidget = TrackingPanelWidget(
            viewer, nplayers_widget=self._nplayers_widget
        )
        self._tab_widget.addTab(
            create_wraper_widget(self._tracking_widget), "Tracking"
        )
