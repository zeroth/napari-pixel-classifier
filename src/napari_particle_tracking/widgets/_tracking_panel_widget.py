"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description: Tracking panel widget for the particle tracking plugin.
"""

import warnings
from typing import TYPE_CHECKING

import napari.layers
import numpy as np
from qtpy.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ._base_widget import BaseWidget
from ._napari_layers_widget import NPLayersWidget
from ._points_filtering_widget import PointsFilteringWidget
from ._tracking_filtering_widget import TrackingFilteringWidget
from ._tracks_analysis_widget import TracksAnaysisWidget
from ._track_quick_analysis_widget import TrackQuickAnaysisWidget

if TYPE_CHECKING:
    import napari


class TrackingPanelWidget(BaseWidget):
    """
    Tracking Panel Widget. This is the main widget for the tracking section.

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

        self._step_tabs = QTabWidget()
        self.layout().addWidget(self._step_tabs)

        self._point_filtering_widget = PointsFilteringWidget(
            self.viewer, self._nplayers_widget
        )
        self._step_tabs.addTab(
            self._point_filtering_widget, "Points Filtering"
        )
        self._tracking_widget = TrackingFilteringWidget(
            self.viewer, self._nplayers_widget
        )
        self._step_tabs.addTab(self._tracking_widget, "Tracking")
        self._tracks_analysis_widget = TracksAnaysisWidget(
            self.viewer, self._nplayers_widget
        )
        self._step_tabs.addTab(self._tracks_analysis_widget, "Tracks Analysis")

        self._track_quick_analysis_widget = TrackQuickAnaysisWidget(
            self.viewer, self._nplayers_widget
        )
        self._step_tabs.addTab(
            self._track_quick_analysis_widget, "Track Quick Analysis"
        )

        self._tracks_analysis_widget.trackSelected.connect(
            self._track_quick_analysis_widget._analyze
        )

        # next prev buttons
        self._next_prev_widget = QWidget()
        self._next_prev_widget.setLayout(QHBoxLayout())
        self.layout().addWidget(self._next_prev_widget)
        # self._next_prev_widget.layout().addWidget(QLabel("Next/Prev"))
        self._next_button = QPushButton("Next")
        self._prev_button = QPushButton("Prev")
        self._next_button.clicked.connect(
            lambda: self._step_tabs.setCurrentIndex(
                (self._step_tabs.currentIndex() + 1) % self._step_tabs.count()
            )
        )
        self._prev_button.clicked.connect(
            lambda: self._step_tabs.setCurrentIndex(
                (self._step_tabs.currentIndex() - 1) % self._step_tabs.count()
            )
        )
        self._next_prev_widget.layout().addWidget(self._prev_button)
        self._next_prev_widget.layout().addWidget(self._next_button)
