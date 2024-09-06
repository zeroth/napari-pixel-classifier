"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description: This is the object filtering module for the particle tracking plugin.
"""

import warnings

import napari.layers
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
from napari.utils import Colormap
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from napari_particle_tracking.libs import histogram, track
from ._filters_widget import create_histogram_filter_widget
from ._base_widget import BaseWidget
from ._napari_layers_widget import NPLayersWidget

# create a color map for the tracks were first color is red with 10% transparency and second color is green with 100% transparency
npcmap = Colormap(colors=["#FF000002", "#00FF00FF"], name="red-green")


class TracksInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout(self)
        self.setLayout(layout)
        self._total_tracks_label = QLabel()
        self.layout().addRow("Total Tracks", self._total_tracks_label)

    def update_info(self, total_tracks):
        self._total_tracks_label.setText(str(total_tracks))


class TrackPyInitWidget(BaseWidget):
    def __init__(
        self,
        viewer: "napari.viewer.Viewer",
        nplayers_widget: NPLayersWidget,
        parent: QWidget = None,
    ):
        super().__init__(viewer, parent)
        self._napari_layers_widget: NPLayersWidget = nplayers_widget

        layout = QFormLayout(self)
        self.setLayout(layout)
        self._serarch_range = QDoubleSpinBox(self)
        self._serarch_range.setMinimum(1)
        self._serarch_range.setValue(10)
        self._serarch_range.setSingleStep(1)
        self._serarch_range.setSuffix(" pixels")
        self.layout().addRow("Search Range", self._serarch_range)

        self._memory = QSpinBox(self)
        self._memory.setMinimum(1)
        self._memory.setValue(5)
        self._memory.setSingleStep(1)
        self._memory.setSuffix(" frames")
        self.layout().addRow("Memory", self._memory)

        self._adaptive_stop = QDoubleSpinBox(self)
        self._adaptive_stop.setMinimum(0.0)
        self._adaptive_stop.setMaximum(1.0)
        self._adaptive_stop.setValue(0.95)
        self._adaptive_stop.setSingleStep(0.01)
        self.layout().addRow("Adaptive Stop", self._adaptive_stop)

        self._track_btn = QPushButton("Track")
        self.layout().addRow(self._track_btn)
        self._track_btn.clicked.connect(self._track)

    def search_range(self):
        return self._serarch_range.value()

    def memory(self):
        return self._memory.value()

    def tracks(self):
        return self._tracks

    def _track(self):
        # get the points layer
        _points_layer: napari.layers.Points = (
            self._napari_layers_widget.get_selected_layers().get(
                "Points", None
            )
        )
        if _points_layer is None:
            warnings.warn("Please select/add a Points layer.")
            return
        _points = _points_layer.data
        _points_properties = _points_layer.features

        _columns = ["y", "x"]
        if "z" in _columns:
            _columns = ["z"] + _columns
        _columns = ["frame"] + _columns
        # get filtered points
        _points_visibility = _points_properties.get("visibility", None)
        if _points_visibility is None:
            warnings.warn("Please filter the points first.")
            return
        _points = _points[_points_visibility == 1]
        _points_pd = pd.DataFrame(_points, columns=_columns)

        # add all the properties after filtering to the points_pd pased on the _points_properties except the visibility
        for _col in _points_properties:
            if _col != "visibility":
                _points_pd[_col] = _points_properties[_col][
                    _points_visibility == 1
                ]

        _tracks = track(
            _points_pd,
            search_range=self.search_range(),
            memory=self.memory(),
            adaptive_stop=self._adaptive_stop.value(),
        )

        _columns = ["track_id"] + _columns
        _tracks_np = _tracks[_columns].to_numpy()

        # add tracks to napari
        # check if tracks_layer exists
        _tracks_layer = self._napari_layers_widget.get_layers().get(
            "Tracks", None
        )
        _tracks_layers_count = 0
        if _tracks_layer is not None:
            _tracks_layers_count = len(_tracks_layer)
        _tracks_layer_name = f"Tracks_{_tracks_layers_count}_{_points_layer.name.removeprefix('Objects_')}"
        _tracks["length"] = _tracks.groupby("track_id")["frame"].transform(
            "size"
        )

        # _tracks.to_csv(f"{_tracks_layer_name}.csv")
        self._tracks = _tracks
        self.viewer.add_tracks(
            _tracks_np,
            name=_tracks_layer_name,
            tail_width=5,
            tail_length=10,
            metadata={"original_tracks_df": _tracks},
        )


class TrackingFilteringWidget(BaseWidget):
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
            if isinstance(layer, napari.layers.Tracks):
                self.add_graph()
        self._nplayers_widget.layerAdded.connect(_layer_added)

        self._track_py_init_widget = TrackPyInitWidget(
            viewer, self._nplayers_widget
        )
        self.layout().addWidget(self._track_py_init_widget)
        self._tracks_info_widget = TracksInfoWidget()
        self.layout().addWidget(self._tracks_info_widget)

        self.filter_track_lenght_widget = create_histogram_filter_widget(
            xlabel="Track Length", ylabel="No of Tracks", title="Track Length Histogram")
        self.filter_track_lenght_widget.rangeChanged.connect(
            self._filter_tracks_length
        )
        self.layout().addWidget(self.filter_track_lenght_widget)
        self.layout().addStretch()
        self.add_graph()

    def _filter_tracks_length(self, vmin, vmax):
        # print(f"Filtering tracks with length between {vmin} and {vmax}")
        if getattr(self, "_tracks_layer", None) is None:
            warnings.warn(
                "Please generate the tracking first. No tracks layer found."
            )
            return

        _oiginal_tracks = self._tracks_layer.metadata["original_tracks_df"]

        # _accepted_index = np.argwhere((_oiginal_tracks["length"] >= vmin) & (_oiginal_tracks["length"] <= vmax))
        _accepted_tracks = _oiginal_tracks[
            (_oiginal_tracks["length"] >= vmin)
            & (_oiginal_tracks["length"] <= vmax)
        ]

        _columns = ["y", "x"]
        if self.tracks.ndim > 4:
            _columns = ["z"] + _columns
        _columns = ["frame"] + _columns
        _columns = ["track_id"] + _columns
        _tracks_np = _accepted_tracks[_columns].to_numpy()
        self._tracks_layer.data = _tracks_np
        self._tracks_layer.refresh()
        self._tracks_info_widget.update_info(
            len(_accepted_tracks.groupby("track_id"))
        )

    def add_graph(self):
        self._tracks_layer: napari.layers.Tracks = (
            self._nplayers_widget.get_selected_layers().get("Tracks", None)
        )
        if self._tracks_layer is None:
            # warnings.warn("Please Initialise the tracking first. No points layer found.")
            return
        self.tracks = self._tracks_layer.data
        self.tracks_properties = self._tracks_layer.metadata[
            "original_tracks_df"
        ]

        # get track lengths
        self.track_lengths = (
            self.tracks_properties.groupby("track_id").size().to_numpy()
        )

        self.filter_track_lenght_widget.plot(self.track_lengths, 1)
        self._tracks_info_widget.update_info(len(self.track_lengths))
