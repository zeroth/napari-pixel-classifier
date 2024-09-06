"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description: Tracking panel widget for the particle tracking plugin.
"""

import warnings
from typing import TYPE_CHECKING

import napari.layers
import numpy as np
from napari.utils import Colormap
from qtpy.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from napari_particle_tracking.libs import ObjectDetection

from ._base_widget import BaseWidget
from ._napari_layers_widget import NPLayersWidget
from ._points_filtering_widget import PointsFilteringWidget
from ._tracking_filtering_widget import TrackingFilteringWidget
from ._tracks_analysis_widget import TracksAnaysisWidget

if TYPE_CHECKING:
    import napari


# simple 2 color colormap
npcmap = Colormap(colors=["#FF000002", "#00FF00FF"], name="red-green")


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
        self.init_btn: QPushButton = QPushButton("(re)Initialize")
        self.layout().addWidget(self.init_btn)
        self.init_btn.clicked.connect(self._initialize)
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

    def _initialize(self):
        selected_layer = self._nplayers_widget.get_selected_layers()
        if selected_layer is None:
            return
        _image_layer: napari.layers.Image = selected_layer.get("Image", None)
        _labels_layer: napari.layers.Labels = selected_layer.get(
            "Labels", None
        )

        if _image_layer is None:
            warnings.warn("Please select/add an Image layer.")
            return
        if _labels_layer is None:
            warnings.warn("Please select/add a Labels layer.")
            return
        if "Prediction" not in _labels_layer.name:
            warnings.warn(
                "You might want to check which labels layer you have selected."
            )

        self.objects_detector = ObjectDetection(
            _image_layer.data, _labels_layer.data
        )
        self.objects = self.objects_detector.detect_objects()
        columns_list = self.objects_detector.get_columns()
        columns = ["y", "x"]
        if "z" in columns_list:
            columns = ["z"] + columns
        columns = ["frame"] + columns
        points = self.objects[columns].to_numpy()

        properties_columns = []
        for column in columns_list:
            if column not in columns:
                properties_columns.append(column)
        # print(properties_columns)
        properties = self.objects[properties_columns].to_dict("list")
        visibitliy = np.ones(len(points))
        properties["visibility"] = visibitliy
        # for key, value in properties.items():
        #     # print(len(properties[key]))
        sizes = properties["equivalent_diameter"]

        symbols = len(sizes) * ["disc"]
        _points_layer_name = f"Objects_{_image_layer.name}"
        p_layer = self.viewer.add_points(
            points,
            name=_points_layer_name,
            features=properties,
            size=sizes,
            face_colormap=npcmap,
            face_color="visibility",
            opacity=0.75,
            symbol=symbols,
            metadata={"original_points_df": self.objects},
        )
        p_layer.editable = False

        # if getattr(self, "_point_filtering_widget", None) is None:
