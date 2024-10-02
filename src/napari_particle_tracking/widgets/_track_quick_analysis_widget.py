import warnings
from functools import partial
from typing import List, Optional, Tuple
from pathlib import Path

import napari.layers
from napari.utils import notifications
import napari.utils
import napari.utils.events
import numpy as np

from qtpy.QtGui import QIntValidator
from qtpy.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QFileDialog
)

from napari_particle_tracking.libs import (
    basic_msd_fit,
    histogram,
    msd,
    msd_fit_function,
)

from ._napari_layers_widget import NPLayersWidget

from ._plots import create_lineplot_widget, colors


class TrackQuickAnaysisWidget(QWidget):
    def __init__(
        self,
        viewer: "napari.viewer.Viewer",
        nplayers_widget: NPLayersWidget,
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self.viewer: napari.viewer.Viewer = viewer
        self._napari_layers_widget: NPLayersWidget = nplayers_widget
        self.setLayout(QVBoxLayout())

        self._plot_scroll = QScrollArea(self)
        self._plot_scroll.setWidgetResizable(True)
        self.layout().addWidget(self._plot_scroll)
    
    def _analyze(self, track_id):
        _tracks_layer: napari.layers.Tracks = self._napari_layers_widget.get_selected_layers().get(
            "Tracks", None
        )

        if _tracks_layer is None:
            warnings.warn("Please select/add a Tracks layer.")
            return

        tracks_df = _tracks_layer.metadata["original_tracks_df"]
        filtered_tracks_df = _tracks_layer.metadata["filtered_tracks_df"]
        tracked_msd = _tracks_layer.metadata["tracked_msd"]
        tracked_msd_fit = _tracks_layer.metadata["tracked_msd_fit"]
        msd_delta = _tracks_layer.metadata["msd_delta"]

        _track = tracks_df[tracks_df["track_id"] == int(track_id)]
        _track_length = len(_track)
        # tracks_df.to_csv("tracks_df.csv")
        # filtered_tracks_df.to_csv("filtered_tracks_df.csv")
        # tracked_msd.to_csv("tracked_msd.csv")
        # tracked_msd_fit.to_csv("tracked_msd_fit.csv")
        print("Quick analysis track_id ", track_id)
        print("tracks_msd ", tracked_msd.columns)

        _track_msd = tracked_msd[tracked_msd["track_id"] == int(track_id)]
        _track_msd.to_csv(f"{track_id}_track_msd.csv")
        _track_msd = _track_msd['msd'].to_numpy()

        _tack_msd_fit = tracked_msd_fit[tracked_msd_fit["track_id"] == int(track_id)]
        _tack_msd_fit = _tack_msd_fit['fit'].to_numpy()

        _track_msd_alpha = tracked_msd_fit[tracked_msd_fit["track_id"] == int(track_id)]
        _track_msd_alpha = _track_msd_alpha['alpha'].to_numpy()[0]
        print("track_id ", track_id, _track_msd.shape)
        _hist_params = [
            {
                "values": [{
                    "x": np.arange(1, len(_track_msd)+1) * msd_delta,
                    "y": _track_msd,
                },
                {
                    "x": np.arange(1, len(_tack_msd_fit)+1) * msd_delta,
                    "y": _tack_msd_fit,
                    }],
                "xlabel": "Time (ms)",
                "ylabel": "MSD",
                "title": f"Track ID : {track_id}, MSD α:{_track_msd_alpha:.3f}",
                "info": f"Tracks Length (frame): {_track_length}",
            },]

        # create lineplot widgets
        _plot_widget = QWidget()
        _plot_widget.setLayout(QVBoxLayout())
        for i, _hist_param in enumerate(_hist_params):
            _hist_param["color"] = colors[i % len(colors)]
            _hist_plot_widget = create_lineplot_widget(**_hist_param)
            _hist_plot_widget.setMinimumWidth(400)
            _hist_plot_widget.setMinimumHeight(400)
            _plot_widget.layout().addWidget(_hist_plot_widget)
            # self._hist_plot_widgets.append(_hist_plot_widget)

        # add eveything to the scroll area
        swid = self._plot_scroll.widget()
        if swid is not None:
            swid.deleteLater()

        self._plot_scroll.setWidget(_plot_widget)

