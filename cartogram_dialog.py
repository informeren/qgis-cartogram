from PyQt4 import QtGui, uic
from qgis.gui import QgsFieldComboBox, QgsMapLayerComboBox

import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'cartogram_dialog.ui'))


class CartogramDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor. Sets up the user interface from QT Designer."""
        super(CartogramDialog, self).__init__(parent)
        self.setupUi(self)
