"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description: This is the object filtering module for the particle tracking plugin.
"""

import warnings

import napari.layers
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ._base_widget import BaseWidget
from ._napari_layers_widget import NPLayersWidget
from ._filters_widget import create_histogram_filter_widget


class PointsInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)
        self.setLayout(layout)
        self._min_intensity_label = QLabel()
        self._max_intensity_label = QLabel()
        self.layout().addRow("Min Intensity", self._min_intensity_label)
        self.layout().addRow("Max Intensity", self._max_intensity_label)

    def update_info(self, min_intensity, max_intensity):
        self._min_intensity_label.setText(str(min_intensity))
        self._max_intensity_label.setText(str(max_intensity))


class PointsFilteringWidget(BaseWidget):
    def __init__(
        self,
        viewer: "napari.viewer.Viewer",
        nplayers_widget: NPLayersWidget,
        parent: QWidget = None,
    ):
        super().__init__(viewer, parent)
        self.setLayout(QVBoxLayout())
        self._nplayers_widget: NPLayersWidget = nplayers_widget
        def _layer_added(name:str, layer: napari.layers.Layer):
            if isinstance(layer, napari.layers.Points):
                self.add_graph()
        self._nplayers_widget.layerAdded.connect(_layer_added)

        self._points_info_widget = PointsInfoWidget()
        self.layout().addWidget(self._points_info_widget)

        self.filter_plot_widget = create_histogram_filter_widget(
            xlabel="Point Diameter", ylabel="Radius", title="Object Radius Histogram")
        self.filter_plot_widget.rangeChanged.connect(self._filter_points)
        self.layout().addWidget(self.filter_plot_widget)
        self.layout().addStretch()
        self.add_graph()

    def _filter_points(self, vmin, vmax):
        print(f"Filtering points with min {vmin} and max {vmax}")
        if getattr(self, "_points_layer", None) is None:
            warnings.warn(
                "Please Initialise the tracking first. No points layer found."
            )
            return

        _accepted_index = np.argwhere(
            (self.points_properties["equivalent_diameter"] >= vmin)
            & (self.points_properties["equivalent_diameter"] <= vmax)
        )

        symbols = ["cross"] * self.points.shape[0]
        visibilities = np.zeros(self.points.shape[0])

        # update symbls and visibilities
        visibilities[_accepted_index] = 1
        self.points_properties["visibility"] = visibilities
        symbols = np.array(symbols)
        symbols[_accepted_index] = "disc"

        self._points_layer.symbol = symbols
        self._points_info_widget.update_info(vmin, vmax)
        self._points_layer.properties = self.points_properties

    def add_graph(self):
        print("Adding point graph")
        self._points_layer: napari.layers.Points = (
            self._nplayers_widget.get_selected_layers().get("Points", None)
        )
        if self._points_layer is None:
            # warnings.warn("Please Initialise the tracking first. No points layer found.")
            return
        self.points = self._points_layer.data
        self.points_properties = self._points_layer.features
        # print(self.points_properties.keys())

        _diameter = self.points_properties.get("equivalent_diameter", None)
        if _diameter is None:
            warnings.warn("Please calculate the intensity and radius first.")
            return

        # diameter bin size is difference between 1st two sorted elements
        _diameter_sorted = np.sort(_diameter)
        _diameter_sorted = np.unique(_diameter_sorted)
        _bin_size = _diameter_sorted[1] - _diameter_sorted[0]

        self.filter_plot_widget.plot(_diameter, _bin_size)
        self._points_info_widget.update_info(
            np.min(_diameter), np.max(_diameter)
        )
