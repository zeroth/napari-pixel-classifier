import warnings
from functools import partial
from typing import List, Optional, Tuple

import napari.layers
import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
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
)

from napari_particle_tracking.libs import (
    basic_msd_fit,
    histogram,
    msd,
    msd_fit_function,
)

from ._napari_layers_widget import NPLayersWidget

colors = ["#DC267F", "#648FFF", "#785EF0", "#FE6100", "#FFB000"]


class HistPlotWidget(QWidget):

    def __init__(
        self, values: np.ndarray, color: str = "#DC267F", histtype: str = "bar"
    ):
        super().__init__()
        layout = QVBoxLayout(self)
        self.color: str = color
        self.values: np.ndarray = values
        self.histtype: str = histtype

        static_canvas = FigureCanvas(Figure(figsize=(3, 2)))
        static_canvas.figure.set_layout_engine("constrained")
        layout.addWidget(NavigationToolbar(static_canvas, self))

        self.infolabel: QLabel = QLabel("")
        self.infolabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.bin_size: QDoubleSpinBox = QDoubleSpinBox()
        self.bin_size.setMinimum(0.001)
        self.bin_size.setValue(1)
        self.bin_size.setSingleStep(0.1)
        self.bin_size.setSuffix(" binsize")
        self.bin_size.setMaximum(np.max(values) - np.min(values))

        layout.addWidget(self.bin_size)
        layout.addWidget(self.infolabel)
        layout.addWidget(static_canvas)

        self.ax: Axes = static_canvas.figure.subplots()

        self.bin_size.valueChanged.connect(self.plot)

        self.title: str = "Title"
        self.xlabel: str = "X"
        self.ylabel: str = "Y"
        self.legends: Optional[List[str]] = None
        self.vspan: List[float] = None

    def clear(self) -> None:
        self.ax.clear()
        self.ax.figure.canvas.draw()

    def set_binsize(self, binsize: float) -> None:
        self.bin_size.setValue(binsize)

    def set_xlabel(self, label: str) -> None:
        self.xlabel = label

    def set_ylabel(self, label: str) -> None:
        self.ylabel = label

    def set_title(self, title: str) -> None:
        self.title = title

    def set_xlim(self, xlim: Tuple[float, float]) -> None:
        self.ax.set_xlim(xlim)

    def set_ylim(self, ylim: Tuple[float, float]) -> None:
        self.ax.set_ylim(ylim)

    def set_vspan_ranges(self, spans: List[float]) -> None:
        self.vspan = spans

    def set_values(self, values: np.ndarray) -> None:
        self.values = values
        self.bin_size.setMaximum(np.max(values) - np.min(values))

    def set_legends(self, legends: Optional[List[str]]) -> None:
        self.legends = legends

    def set_histtype(self, histtype: str) -> None:
        self.histtype = histtype

    def set_infolabel(self, label: str) -> None:
        self.infolabel.setText(label)

    def plot(self) -> None:
        if self.values is None:
            return
        self.clear()
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.set_title(self.title)
        values = self.values
        if self.histtype == "bar":
            h, bins, _ = histogram(values, float(self.bin_size.value()))
            self.ax.hist(
                values,
                bins=bins,
                edgecolor="black",
                linewidth=0.5,
                color=self.color,
                alpha=0.5,
            )
            self.ax.grid()
        elif self.histtype == "line":
            h, bins, _ = histogram(values, float(self.bin_size.value()))
            self.ax.plot(bins[:-1], h, color=self.color)
            self.ax.grid()

        if isinstance(self.vspan, list):
            if self.legends is not None and isinstance(self.legends, list):
                for i in range(1, len(self.vspan)):
                    self.ax.axvspan(
                        self.vspan[i - 1],
                        self.vspan[i],
                        color=colors[(i - 1) % len(self.vspan)],
                        alpha=0.5,
                        label=self.legends[i - 1],
                    )
                self.ax.legend()
                self.ax.legend(loc="upper right")
        else:
            if (self.legends is not None) and (
                not isinstance(self.legends, list)
            ):
                self.ax.set_label(self.legends)
                self.ax.legend()
                self.ax.legend(loc="upper right")
        self.ax.figure.canvas.draw()


def create_histogram_widget(
    values: np.ndarray,
    binsize: float,
    color: str = "#DC267F",
    xlabel: str = "X",
    ylabel: str = "Y",
    title: str = "Title",
    histtype: str = "bar",
    info: str = "",
    legends: Optional[List[str]] = None,
    vspan: Optional[List[float]] = None,
) -> HistPlotWidget:
    """
    Factory function to create a histogram widget

    Parameters
    ----------
    values : np.ndarray
        values to be plotted
    binsize : float
        binsize for the histogram
    color : str, optional
        color of the plot, by default "#DC267F"
    xlabel : str, optional
        xlabel, by default "X"
    ylabel : str, optional
        ylabel, by default "Y"
    title : str, optional
        title of the plot, by default "Title"
    histtype : str, optional
        type of the histogram, by default "bar"
    legends : list, optional
        legends for the plot, by default None
    vspan : list, optional
        vertical span ranges, by default None

    Returns
    -------
    HistPlotWidget
        The created histogram widget
    """
    _hist_plot_widget = HistPlotWidget(values, color=color, histtype=histtype)
    _hist_plot_widget.clear()
    _hist_plot_widget.set_xlabel(xlabel)
    _hist_plot_widget.set_ylabel(ylabel)
    _hist_plot_widget.set_title(title)
    _hist_plot_widget.set_binsize(binsize)
    _hist_plot_widget.set_legends(legends)
    _hist_plot_widget.set_vspan_ranges(vspan)
    _hist_plot_widget.set_infolabel(info)
    _hist_plot_widget.plot()
    return _hist_plot_widget


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

        self._plot_scroll = QScrollArea(self)
        self._plot_scroll.setWidgetResizable(True)
        self.layout().addRow(self._plot_scroll)

    def _analyze(self):
        # get the tracks layer
        _tracks_layer: napari.layers.Tracks = (
            self._napari_layers_widget.get_selected_layers().get(
                "Tracks", None
            )
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
