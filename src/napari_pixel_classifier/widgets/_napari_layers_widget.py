"""
Author: Abhishek Patil <abhishek@zeroth.me>

Description:

This module contains the implementation of the `NPLayersWidget` and `NPLayerWidget` classes.
NPLayersWidget:
    A widget that allows the user to select layers from a napari viewer.
NPLayerWidget:
    A widget that represents a single layer selection in the NPLayersWidget.



"""

from typing import Dict, List, Optional, Type

import napari
import napari.layers
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QComboBox, QFormLayout, QVBoxLayout, QWidget, QPushButton

from ._base_widget import BaseWidget

_known_napari_layers_types = {
    "Image": napari.layers.Image,
    "Labels": napari.layers.Labels,
    "Points": napari.layers.Points,
    "Vectors": napari.layers.Vectors,
    "Shapes": napari.layers.Shapes,
    "Surface": napari.layers.Surface,
    "Tracks": napari.layers.Tracks,
}


def find_layer_type(layer: napari.layers.Layer) -> str:
    for key, value in _known_napari_layers_types.items():
        if isinstance(layer, value):
            return key
    return "Unknown"


class tmpEvent:
    def __init__(self, value, index):
        self.value = value
        self.index = index


class NPLayerWidget(BaseWidget):
    def __init__(
        self,
        viewer: "napari.viewer.Viewer",
        layer_type_name: str,
        np_type: type,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(viewer, parent)
        self.np_type = np_type
        self.layer_type_name = layer_type_name
        self._combo_box = QComboBox()
        self._layer_names = []
        for index, layer in enumerate(self.viewer.layers):
            if isinstance(layer, self.np_type):
                self._combo_box.addItem(layer.name, index)
                self._layer_names.append(layer.name)

        self.setLayout(QFormLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addRow(layer_type_name, self._combo_box)

        # self.viewer.layers.events.inserted.connect(self._update_layers)
        # self.viewer.layers.events.removed.connect(self._update_layers)
        # self.viewer.layers.selection.events.changed.connect(self._check_name_update)

    def _update_layers(self):
        self._combo_box.clear()
        self._layer_names = []

        for index, layer in enumerate(self.viewer.layers):
            if isinstance(layer, self.np_type):
                self._combo_box.addItem(layer.name, index)
                self._layer_names.append(layer.name)

    def _check_name_update(self, event):
        for layer in self.viewer.layers:
            if layer.name not in self._layer_names and isinstance(
                layer, self.np_type
            ):
                self._update_layers()

    def get_selected_layer(self):
        if self._combo_box.count() == 0:
            return None
        return self.viewer.layers[self._combo_box.currentText()]

    def get_layer_count(self):
        return self._combo_box.count()


class NPLayersWidget(BaseWidget):
    """
    A widget for managing layers in a napari viewer.
    Parameters:
    -----------
    viewer : napari.viewer.Viewer
        The napari viewer instance.
    parent : None
        The parent widget.
    **kwargs : dict
        Additional keyword arguments.

    Methods:
    --------
    get_selected_layers() -> dict[str, napari.layers.Layer]
        Returns a dictionary of selected layers.
        example:
            {
                "Image": napari.layers.Image (layer instance),
                "Labels": napari.layers.Labels (layer instance),
            }
    """

    layerAdded = Signal(str, napari.layers.Layer)
    layerRemoved = Signal(str, napari.layers.Layer)

    def __init__(
        self,
        viewer: "napari.viewer.Viewer",
        parent: Optional[QWidget] = None,
        **kwargs: Type[napari.layers.Layer],
    ) -> None:
        super().__init__(viewer, parent)

        self.setLayout(QVBoxLayout())
        self._separate_layers_button = QPushButton("Separate Layers")
        self._separate_layers_button.clicked.connect(self.separate_layers)
        self.layout().addWidget(self._separate_layers_button)

        self._layers_combo: Dict[str, Type[napari.layers.Layer]] = {}

        self.viewer.layers.events.inserted.connect(self._layer_added)
        self.viewer.layers.events.removed.connect(self._layer_removed)

        for layer in self.viewer.layers:
            _layer_type_name = find_layer_type(layer)
            if _layer_type_name not in self._layers_combo.keys():
                self.add_layer(
                    _layer_type_name,
                    _known_napari_layers_types[_layer_type_name],
                    layer,
                )
            else:
                self._layers_combo[_layer_type_name]._update_layers()

    def get_selected_layers(self) -> Dict[str, napari.layers.Layer]:
        return {
            dt_name: self._layers_combo[dt_name].get_selected_layer()
            for dt_name in self._layers_combo.keys()
        }

    def get_layers(self) -> Dict[str, List[napari.layers.Layer]]:
        result = {}
        for dt_name in self._layers_combo.keys():
            result[dt_name] = [
                layer
                for layer in self.viewer.layers
                if find_layer_type(layer) == dt_name
            ]
        return result
    
    def add_layer(
        self, layer_type_name: str, np_type: Type[napari.layers.Layer], layer: napari.layers.Layer
    ):
        self._layers_combo[layer_type_name] = NPLayerWidget(
            self.viewer, layer_type_name, np_type, self
        )
        self.layout().addWidget(self._layers_combo[layer_type_name])
        self._layers_combo[layer_type_name]._update_layers()
        self.layerAdded.emit(layer_type_name, layer)

    def remove_layer(self, layer_type_name: str, layer: napari.layers.Layer):
        # print("remove_layer", layer_type_name)
        self.layout().removeWidget(self._layers_combo[layer_type_name])
        del self._layers_combo[layer_type_name]
        self.layerRemoved.emit(layer_type_name, layer)

    def _layer_added(self, event):
        _layer = event.value
        _layer_type_name = find_layer_type(_layer)
        if _layer_type_name not in self._layers_combo.keys():
            self.add_layer(
                _layer_type_name, _known_napari_layers_types[_layer_type_name], _layer
            )
        else:
            self._layers_combo[_layer_type_name]._update_layers()

    def _layer_removed(self, event):
        # print("Layer removed", event.value.name)
        _layer = event.value
        _layer_type_name = find_layer_type(_layer)
        if _layer_type_name in self._layers_combo.keys():
            self._layers_combo[_layer_type_name]._update_layers()
            # print("Found the layer type in the dictionary", "layer count is: ", self._layers_combo[_layer_type_name].get_layer_count(), "count type ", type(self._layers_combo[_layer_type_name].get_layer_count()))
            if self._layers_combo[_layer_type_name].get_layer_count() == 0:
                self.remove_layer(_layer_type_name, _layer)
    
    def separate_layers(self):
        if("Image" in self._layers_combo.keys()):
            image_layer = self._layers_combo["Image"].get_selected_layer()
            if(image_layer is not None and isinstance(image_layer, napari.layers.Image)):
                image_data = image_layer.data
                if(len(image_data.shape) == 4):
                    # find channel axis. Logic is min from 1st two axes
                    channel_axis = 0 if image_data.shape[0] < image_data.shape[1] else 1
                    if channel_axis != 0:
                        image_data = image_data.swapaxes(0, channel_axis)
                    for i in range(image_data.shape[0]):
                        new_layer = napari.layers.Image(image_data[i], name=f"channel_{i}_{image_layer.name}")
                        self.viewer.add_layer(new_layer)
                    self.viewer.layers.remove(image_layer)