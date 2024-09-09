import warnings
from functools import partial
from typing import List, Optional, Tuple

import napari.layers
from napari.utils import notifications
import numpy as np

from qtpy.QtGui import QIntValidator
from qtpy.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
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

from ._plots import create_histogram_widget, colors


class TracksAnaysisWidget(QWidget):
    def __init__(
        self,
        viewer: "napari.viewer.Viewer",
        nplayers_widget: NPLayersWidget,
        parent: QWidget = None,
    ):
        super().__init__(parent)
        self.viewer: napari.viewer.Viewer = viewer
        self._napari_layers_widget: NPLayersWidget = nplayers_widget
        self.setLayout(QFormLayout())

        self._timedelay = QDoubleSpinBox(self)
        self._timedelay.setMinimum(0)
        self._timedelay.setValue(5)
        self._timedelay.setSingleStep(1)
        self._timedelay.setSuffix(" ms")
        self.layout().addRow("Time Delay", self._timedelay)

        self._max_try = QLineEdit(self)
        self._max_try.setText("1000000")
        self._max_try.setValidator(QIntValidator())
        self.layout().addRow("Max Try for msd_fit", self._max_try)

        self._intensity_option = QComboBox(self)
        options = [
            {"text": "Max Intensity", "userData": "max_intensity"},
            {"text": "Mean Intensity", "userData": "mean_intensity"},
            {"text": "Min Intensity", "userData": "min_intensity"},
        ]
        for option in options:
            self._intensity_option.addItem(option["text"], option["userData"])
        self.layout().addRow("Intensity Option", self._intensity_option)

        self._btn_analyze = QPushButton("Analyze")
        self.layout().addRow(self._btn_analyze)
        self._btn_analyze.clicked.connect(self._analyze)

        self._btn_download = QPushButton("Download")
        self.layout().addRow(self._btn_download)
        self._btn_download.clicked.connect(self._download)

        self._plot_scroll = QScrollArea(self)
        self._plot_scroll.setWidgetResizable(True)
        self.layout().addRow(self._plot_scroll)

    def _download(self):
        # get the tracks layer
        _tracks_layer: napari.layers.Tracks = self._napari_layers_widget.get_selected_layers().get(
            "Tracks", None
        )

        if _tracks_layer is None:
            warnings.warn("Please select/add a Tracks layer.")
            return
        
        tracks_df = _tracks_layer.metadata["original_tracks_df"]

        save_path = QFileDialog.getSaveFileName(self, "Save File", "", "CSV (*.csv)")[0]
        if save_path:
            tracks_df.to_csv(save_path, index=False)
            notifications.show_info(f"Tracks saved successfully at {save_path}")
        

    def _analyze(self):
        # get the tracks layer
        _tracks_layer: napari.layers.Tracks = self._napari_layers_widget.get_selected_layers().get(
            "Tracks", None
        )

        if _tracks_layer is None:
            warnings.warn("Please select/add a Tracks layer.")
            return

        _intensity_filter = self._intensity_option.currentData()
        _intensity_filter_type = self._intensity_option.currentText()

        # get tracks df from the layers metadata filter it to the current tracks

        tracks_df = _tracks_layer.metadata["original_tracks_df"]
        current_tracks = _tracks_layer.data
        current_track_ids = current_tracks[:, 0]
        current_tracks_df = tracks_df[
            tracks_df["track_id"].isin(current_track_ids)
        ]

        # get track lengths
        track_lengths = current_tracks_df.groupby("track_id").size().to_numpy()

        # get track mean intensity
        track_mean_intensity = (
            current_tracks_df.groupby("track_id")[_intensity_filter]
            .mean()
            .to_numpy()
        )
        binsize = 100 if np.mean(track_mean_intensity) >= 1000 else 5

        # get track msd
        current_track_msd = None
        # check if the tracks have z
        if "z" in current_tracks_df.columns:
            # get msd for 3D todo have a corrent distance calculation
            current_track_msd = current_tracks_df.groupby(
                "track_id", group_keys=True
            ).apply(lambda x: msd(x[["x", "y", "z"]].to_numpy()))
        else:
            current_track_msd = current_tracks_df.groupby(
                "track_id", group_keys=True
            ).apply(lambda x: msd(x[["x", "y"]].to_numpy()))

        # fit the msd
        _basic_fit_partial = partial(
            basic_msd_fit,
            delta=float(self._timedelay.value()),
            fit_function=msd_fit_function,
            maxfev=int(self._max_try.text()),
        )

        current_track_fit_df = current_track_msd.groupby(
            "track_id", group_keys=True
        ).apply(lambda x: _basic_fit_partial(x.to_numpy()))
        current_track_fit = current_track_fit_df.to_numpy()

        _confined_tracks = current_track_fit_df[
            current_track_fit_df < 0.4
        ].index.to_numpy()
        _diffusive_tracks = current_track_fit_df[
            (current_track_fit_df >= 0.4) & (current_track_fit_df <= 1.2)
        ].index.to_numpy()
        _directed_tracks = current_track_fit_df[
            current_track_fit_df > 1.2
        ].index.to_numpy()

        # get mean intensity for each category
        _mean_intensity_confined = (
            current_tracks_df[
                current_tracks_df["track_id"].isin(_confined_tracks)
            ]
            .groupby("track_id")[_intensity_filter]
            .mean()
            .to_numpy()
        )
        _mean_intensity_diffusive = (
            current_tracks_df[
                current_tracks_df["track_id"].isin(_diffusive_tracks)
            ]
            .groupby("track_id")[_intensity_filter]
            .mean()
            .to_numpy()
        )
        _mean_intensity_directed = (
            current_tracks_df[
                current_tracks_df["track_id"].isin(_directed_tracks)
            ]
            .groupby("track_id")[_intensity_filter]
            .mean()
            .to_numpy()
        )

        print(f"Total Tracks: {len(track_lengths)}")
        # create dict to store parameters for histogram widget to be created
        _hist_params = [
            {
                "values": track_lengths,
                "binsize": 1,
                "xlabel": "Length",
                "ylabel": "Number of Tracks",
                "title": "Track Length Histogram",
                "histtype": "bar",
                "info": f"Total Tracks: {len(track_lengths)}",
            },
            {
                "values": track_mean_intensity,
                "binsize": binsize,
                "xlabel": _intensity_filter_type,
                "ylabel": "Number of Tracks",
                "title": f"Track {_intensity_filter_type} Histogram",
                "histtype": "bar",
                "info": f"Total Tracks: {len(track_mean_intensity)}",
            },
            {
                "values": current_track_fit,
                "binsize": 0.1,
                "xlabel": "MSD α",
                "ylabel": "Number of Tracks",
                "title": "Track MSD Fit",
                "histtype": "line",
                "legends": [
                    "Confined α < 0.4",
                    "Diffusive 0.4 < α < 1.2",
                    "Directed α > 1.2",
                ],
                "vspan": [
                    np.min(current_track_fit),
                    0.4,
                    1.2,
                    np.max(current_track_fit),
                ],
                "info": f"Total confiend: {len(_confined_tracks)}, diffusive: {len(_diffusive_tracks)}, directed: {len(_directed_tracks)}",
            },
            {
                "values": _mean_intensity_confined,
                "binsize": binsize,
                "xlabel": _intensity_filter_type,
                "ylabel": "Number of Tracks",
                "title": f"Track {_intensity_filter_type} Confined Histogram",
                "histtype": "bar",
                "info": f"Total Tracks: {len(_mean_intensity_confined)}",
            },
            {
                "values": _mean_intensity_diffusive,
                "binsize": binsize,
                "xlabel": _intensity_filter_type,
                "ylabel": "Number of Tracks",
                "title": f"Track {_intensity_filter_type} Diffusive Histogram",
                "histtype": "bar",
                "info": f"Total Tracks: {len(_mean_intensity_diffusive)}",
            },
            {
                "values": _mean_intensity_directed,
                "binsize": binsize,
                "xlabel": _intensity_filter_type,
                "ylabel": "Number of Tracks",
                "title": f"Track {_intensity_filter_type} Directed Histogram",
                "histtype": "bar",
                "info": f"Total Tracks: {len(_mean_intensity_directed)}",
            },
        ]

        # create histogram widgets
        _plot_widget = QWidget()
        _plot_widget.setLayout(QVBoxLayout())
        for i, _hist_param in enumerate(_hist_params):
            _hist_param["color"] = colors[i % len(colors)]
            _hist_plot_widget = create_histogram_widget(**_hist_param)
            _hist_plot_widget.setMinimumWidth(400)
            _hist_plot_widget.setMinimumHeight(400)
            _plot_widget.layout().addWidget(_hist_plot_widget)
            # self._hist_plot_widgets.append(_hist_plot_widget)

        # self._track_mean_intensity_directed_hitogram = HistPlotWidget(color=colors[_graph_count % len(colors)])
        # self._track_mean_intensity_directed_hitogram.clear()
        # self._track_mean_intensity_directed_hitogram.set_xlabel("Mean Intensity")
        # self._track_mean_intensity_directed_hitogram.set_ylabel("Number of Tracks")
        # self._track_mean_intensity_directed_hitogram.set_title("Track Mean Intensity Directed Histogram")
        # self._track_mean_intensity_directed_hitogram.set_values(_mean_intensity_directed)
        # self._track_mean_intensity_directed_hitogram.set_binsize(binsize)
        # self._track_mean_intensity_directed_hitogram.set_infolabel(f"Toal Tracks: {len(_mean_intensity_directed)}")
        # self._track_mean_intensity_directed_hitogram.plot()
        # self._track_mean_intensity_directed_hitogram.setMinimumWidth(400)
        # self._track_mean_intensity_directed_hitogram.setMinimumHeight(400)
        # _plot_widget.layout().addWidget(self._track_mean_intensity_directed_hitogram)
        # _graph_count += 1

        # add eveything to the scroll area
        swid = self._plot_scroll.widget()
        if swid is not None:
            swid.deleteLater()

        self._plot_scroll.setWidget(_plot_widget)
