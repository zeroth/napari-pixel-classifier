import numpy as np

from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector

from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QVBoxLayout,
    QWidget,
)

from napari_particle_tracking.libs import histogram


class HistogramFilterWidget(QWidget):
    rangeChanged = Signal(float, float)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        static_canvas = FigureCanvas(Figure(figsize=(3, 2)))

        static_canvas.figure.set_layout_engine("constrained")
        layout.addWidget(NavigationToolbar(static_canvas, self))
        layout.addWidget(static_canvas)

        self.values = None
        self.bin_size = 1
        self.ax = static_canvas.figure.subplots()

        self.span = SpanSelector(
            self.ax,
            self.onselect,
            "horizontal",
            grab_range=2,
            useblit=True,
            props={"facecolor": "blue", "alpha": 0.5},
            interactive=True,
        )

        self.vmin = 0
        self.vmax = 0

    def onselect(self, vmin, vmax):
        self.vmin = vmin
        self.vmax = vmax

        self.rangeChanged.emit(vmin, vmax)

    def set_xlabels(self, xlabel):
        self.ax.set_xlabel(xlabel)

    def set_ylabels(self, ylabel):
        self.ax.set_ylabel(ylabel)

    def set_title(self, title):
        self.ax.set_title(title)

    def plot(self, values, bin_size=1):
        self.ax.clear()
        self.values = values
        self.bin_size = bin_size
        _, edges, _ = histogram(self.values, binsize=self.bin_size)
        self.ax.hist(
            self.values,
            bins=edges,
            edgecolor="black",
            linewidth=0.5,
            color="#DC267F",
            alpha=0.5,
        )

        self.ax.grid()
        self.ax.figure.canvas.draw()
        self.vmin = np.min(self.values)
        self.vmax = np.max(self.values)
        self.span.extents = (self.vmin, self.vmax)


def create_histogram_filter_widget(xlabel="Values", ylabel="Frequency", title="Histogram"):
    widget = HistogramFilterWidget()
    widget.set_xlabels(xlabel)
    widget.set_ylabels(ylabel)
    widget.set_title(title)
    return widget
