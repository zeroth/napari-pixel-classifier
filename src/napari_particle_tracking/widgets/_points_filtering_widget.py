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


class FilterPlotWidget(QWidget):
    rangeChanged = Signal(float, float)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        static_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        # Ideally one would use self.addToolBar here, but it is slightly
        # incompatible between PyQt6 and other bindings, so we just add the
        # toolbar as a plain widget instead.
        static_canvas.figure.set_layout_engine("constrained")
        layout.addWidget(NavigationToolbar(static_canvas, self))
        layout.addWidget(static_canvas)

        self.ax = static_canvas.figure.subplots()
        # t = np.linspace(0, 10, 501)

        self.span = SpanSelector(
            self.ax,
            self.onselect,
            "horizontal",
            grab_range=2,
            useblit=True,
            props=dict(facecolor="blue", alpha=0.5),
            interactive=True,
        )
        # layout.addWidget(span)
        self.vmin = 0
        self.vmax = 0

    def onselect(self, vmin, vmax):
        self.vmin = vmin
        self.vmax = vmax

        self.rangeChanged.emit(vmin, vmax)

    def plot(self, x, y):
        self.ax.clear()
        self.ax.plot(x, y)
        self.ax.set_xlim(np.min(x), np.max(x))
        self.ax.set_ylim(np.min(y), np.max(y))
        self.ax.set_xlabel("Intensity")
        # self.ax.set_xscale("log")
        self.ax.set_ylabel("Radius")
        # self.ax.set_yscale("log")
        self.ax.set_title("Intensity vs Radius")
        self.ax.grid()
        self.ax.figure.canvas.draw()
        self.vmin = np.min(x)
        self.vmax = np.max(x)
        self.span.extents = (self.vmin, self.vmax)


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
        self._nplayers_widget.layerAdded.connect(self.add_graph)

        self._points_info_widget = PointsInfoWidget()
        self.layout().addWidget(self._points_info_widget)

        self.filter_plot_widget = FilterPlotWidget()
        self.filter_plot_widget.rangeChanged.connect(self._filter_points)
        self.layout().addWidget(self.filter_plot_widget)
        self.layout().addStretch()
        self.add_graph()

    def _filter_points(self, vmin, vmax):
        if getattr(self, "_points_layer", None) is None:
            warnings.warn(
                "Please Initialise the tracking first. No points layer found."
            )
            return

        _accepted_index = np.argwhere(
            (self.points_properties["mean_intensity"] >= vmin)
            & (self.points_properties["mean_intensity"] <= vmax)
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
        self._points_layer: napari.layers.Points = (
            self._nplayers_widget.get_selected_layers().get("Points", None)
        )
        if self._points_layer is None:
            # warnings.warn("Please Initialise the tracking first. No points layer found.")
            return
        self.points = self._points_layer.data
        self.points_properties = self._points_layer.features
        # print(self.points_properties.keys())
        _intensity = self.points_properties.get("mean_intensity", None)
        _radius = self.points_properties.get("radius", None)
        if _intensity is None or _radius is None:
            warnings.warn("Please calculate the intensity and radius first.")
            return

        _zip_list = zip(_intensity, _radius)
        _zip_list = sorted(_zip_list, key=lambda x: x[0])
        _intensity, _radius = zip(*_zip_list)
        self.filter_plot_widget.plot(_intensity, _radius)
        self._points_info_widget.update_info(
            np.min(_intensity), np.max(_intensity)
        )
