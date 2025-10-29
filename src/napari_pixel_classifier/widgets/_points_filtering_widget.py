"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description: This is the object filtering module for the particle tracking plugin.
"""

import warnings

import napari.layers
from napari.utils import progress
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
from qtpy.QtCore import Signal, Qt
from qtpy.QtWidgets import (
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QPushButton,
)

from ._base_widget import BaseWidget
from ._napari_layers_widget import NPLayersWidget
from ._filters_widget import create_histogram_filter_widget

from napari_pixel_classifier.libs import ObjectDetection

from napari.utils import Colormap
# simple 2 color colormap
npcmap = Colormap(colors=["#FF000002", "#00FF00FF"], name="red-green")


class PointsInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)
        self.setLayout(layout)
        self._min_intensity_label = QLabel()
        self._max_intensity_label = QLabel()
        self.layout().addRow("Min", self._min_intensity_label)
        self.layout().addRow("Max", self._max_intensity_label)

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

        def _layer_added(name: str, layer: napari.layers.Layer):
            if isinstance(layer, napari.layers.Points):
                self.add_graph()
        self._nplayers_widget.layerAdded.connect(_layer_added)

        self.init_btn: QPushButton = QPushButton("(re)Initialize")
        self.layout().addWidget(self.init_btn)
        self.init_btn.clicked.connect(self._initialize)

        # add horizontal line
        _divider = QLabel()
        _divider.setTextFormat(Qt.RichText)
        _divider.setText("<hr><b>Filter points by Diameter</b>")
        self.layout().addWidget(_divider)

        self._points_info_widget = PointsInfoWidget()
        self.layout().addWidget(self._points_info_widget)

        self.filter_plot_widget = create_histogram_filter_widget(
            xlabel="Point Diameter", ylabel="Radius", title="Object Radius Histogram", color="#648FFF")
        self.filter_plot_widget.rangeChanged.connect(self._filter_points)
        self.layout().addWidget(self.filter_plot_widget)
        self.layout().addStretch()
        self.add_graph()

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
        self.objects = self.objects_detector.detect_objects(progress=progress)
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

        _points_layer = self._nplayers_widget.get_layers().get(
            "Points", None
        )

        if _points_layer is not None:
            self.viewer.layers.remove(_points_layer[0])

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

    def _filter_points(self, vmin, vmax):
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

        self.filter_plot_widget.set_values(_diameter)
        self.filter_plot_widget.set_bin_size_range(
            0, np.max(_diameter) + _bin_size)
        self.filter_plot_widget.set_bin_size(_bin_size)
        self.filter_plot_widget.plot()
        self._points_info_widget.update_info(
            np.min(_diameter), np.max(_diameter)
        )
