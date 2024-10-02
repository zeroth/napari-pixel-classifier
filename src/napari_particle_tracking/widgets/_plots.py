from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure

from typing import List, Optional, Tuple

import numpy as np

from qtpy.QtWidgets import (
    QDoubleSpinBox,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from napari_particle_tracking.libs import (
    histogram,
)

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


class LinePlotWidget(QWidget):

    def __init__(
        self, values: np.ndarray, color: str = "#DC267F"
    ):
        super().__init__()
        layout = QVBoxLayout(self)
        self.color: str = color
        self.values: np.ndarray = values
        

        static_canvas = FigureCanvas(Figure(figsize=(3, 2)))
        static_canvas.figure.set_layout_engine("constrained")
        layout.addWidget(NavigationToolbar(static_canvas, self))

        self.infolabel: QLabel = QLabel("")
        self.infolabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout.addWidget(self.infolabel)
        layout.addWidget(static_canvas)

        self.ax: Axes = static_canvas.figure.subplots()

        self.title: str = "Title"
        self.xlabel: str = "X"
        self.ylabel: str = "Y"
        self.legends: Optional[List[str]] = None
        self.vspan: List[float] = None

    def clear(self) -> None:
        self.ax.clear()
        self.ax.figure.canvas.draw()


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

    def set_infolabel(self, label: str) -> None:
        self.infolabel.setText(label)

    def plot(self) -> None:
        if self.values is None:
            return
        self.clear()
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.set_title(self.title)
        data = self.values
        if isinstance(data, list):
            for i, d in enumerate( data):
                if 'x' not in d:
                    y = d['y']
                    x = np.arange(len(y))
                else:
                    x = d['x']
                    y = d['y']
                self.ax.plot(x, y, color= colors[i % len(colors)])
        else:
            d = data
            if 'x' not in d:
                y = d['y']
                x = np.arange(len(y))
            else:
                x = d['x']
                y = d['y']
            self.ax.plot(x, y, color= self.color)

        # self.ax.plot(
        #         values,
        #         linewidth=0.5,
        #         color=self.color,
        #         alpha=0.5,
        #     )
        # self.ax.grid()
        
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

def create_lineplot_widget(
    values: np.ndarray,
    color: str = "#DC267F",
    xlabel: str = "X",
    ylabel: str = "Y",
    title: str = "Title",
    info: str = "",
    legends: Optional[List[str]] = None,
    vspan: Optional[List[float]] = None,
) -> LinePlotWidget:
    """
    Factory function to create a histogram widget

    Parameters
    ----------
    values : np.ndarray
        values to be plotted
    color : str, optional
        color of the plot, by default "#DC267F"
    xlabel : str, optional
        xlabel, by default "X"
    ylabel : str, optional
        ylabel, by default "Y"
    title : str, optional
        title of the plot, by default "Title"
    legends : list, optional
        legends for the plot, by default None
    vspan : list, optional
        vertical span ranges, by default None

    Returns
    -------
    LinePlotWidget
        The created lineplot widget
    """
    _line_plot_widget = LinePlotWidget(values, color=color)
    _line_plot_widget.clear()
    _line_plot_widget.set_xlabel(xlabel)
    _line_plot_widget.set_ylabel(ylabel)
    _line_plot_widget.set_title(title)
    _line_plot_widget.set_legends(legends)
    _line_plot_widget.set_vspan_ranges(vspan)
    _line_plot_widget.set_infolabel(info)
    _line_plot_widget.plot()
    return _line_plot_widget