"""
Author: Abhishek Patil <abhishek@zeroth.me>
Description:  BaseWidget class for the particle tracking plugin.
"""

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QVBoxLayout, QWidget

if TYPE_CHECKING:
    import napari


def create_wraper_widget(widget: QWidget) -> QWidget:
    """
    Create a wrapper widget that will contain the given widget.
    This is just a convenience function to add a stretch factor to the given widget when adding to tab widget.
    """

    class WrapperWidget(QWidget):
        def __init__(self, w: QWidget) -> None:
            super().__init__()
            self.setLayout(QVBoxLayout())
            self.layout().addWidget(w)
            # self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            # self.layout().addStretch()

    return WrapperWidget(widget)


class BaseWidget(QWidget):
    def __init__(
        self, viewer: "napari.viewer.Viewer", parent: QWidget = None
    ) -> None:
        super().__init__(parent=parent)
        self.viewer: napari.viewer.Viewer = viewer
        # self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
