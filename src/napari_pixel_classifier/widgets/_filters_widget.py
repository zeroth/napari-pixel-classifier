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
    QDoubleSpinBox
)

from napari_pixel_classifier.libs import histogram


class HistogramFilterWidget(QWidget):
    rangeChanged = Signal(float, float)

    def __init__(self, color="#DC267F"):
        super().__init__()
        layout = QVBoxLayout(self)
        self.color = color

        static_canvas = FigureCanvas(Figure(figsize=(3, 2)))

        static_canvas.figure.set_layout_engine("constrained")
        layout.addWidget(NavigationToolbar(static_canvas, self))

        self._bin_size_control = QDoubleSpinBox(self)
        self._bin_size_control.setMinimum(0)
        self._bin_size_control.setMaximum(100)
        self._bin_size_control.setValue(1)
        self._bin_size_control.setSingleStep(1)
        self._bin_size_control.valueChanged.connect(self.plot)
        
        layout.addWidget(self._bin_size_control)
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
        self.title: str = "Filter"
        self.xlabel: str = "X"
        self.ylabel: str = "Y"

    def onselect(self, vmin, vmax):
        self.vmin = vmin
        self.vmax = vmax

        self.rangeChanged.emit(vmin, vmax)

    def set_xlabel(self, label: str) -> None:
        self.xlabel = label

    def set_ylabel(self, label: str) -> None:
        self.ylabel = label

    def set_title(self, title: str) -> None:
        self.title = title

    def set_bin_size(self, bin_size):
        # disconnect the signal to avoid calling plot twice
        self._bin_size_control.valueChanged.disconnect(self.plot)
        self._bin_size_control.setValue(bin_size)
        self._bin_size_control.valueChanged.connect(self.plot)
    
    def set_bin_size_range(self, min_bin_size, max_bin_size):
        self._bin_size_control.setMinimum(min_bin_size)
        self._bin_size_control.setMaximum(max_bin_size)
    
    def set_values(self, values):
        self.values = values
    
    def plot(self, values = None, bin_size=None):
        if self.values is None:
            return
        self.ax.clear()
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.set_title(self.title)
        # self.values = values
        self.bin_size = float(self._bin_size_control.value())
        
        _, edges, _ = histogram(self.values, binsize=self.bin_size)
        
        self.ax.hist(
            self.values,
            bins=edges,
            edgecolor="black",
            linewidth=0.5,
            color=self.color,
            alpha=0.5,
        )

        self.ax.grid()
        self.ax.figure.canvas.draw()
        self.vmin = np.min(self.values)
        self.vmax = np.max(self.values)
        self.span.extents = (self.vmin, self.vmax)


def create_histogram_filter_widget(xlabel="Values", ylabel="Frequency", title="Histogram", color="#DC267F"):
    widget = HistogramFilterWidget(color=color)
    widget.set_xlabel(xlabel)
    widget.set_ylabel(ylabel)
    widget.set_title(title)
    return widget
