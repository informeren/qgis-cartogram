from PyQt4.QtCore import (Qt, QCoreApplication, QSettings, QThread,
    QTranslator, qVersion)
from PyQt4.QtGui import (QAction, QPushButton, QDialog, QFileDialog, QIcon,
    QLabel, QMessageBox, QProgressBar)
from qgis.core import (QGis, QgsDistanceArea, QgsGeometry, QgsMapLayer,
    QgsMapLayerRegistry, QgsMessageLog, QgsPoint, QgsVectorFileWriter,
    QgsVectorLayer)
from qgis.gui import QgsFieldProxyModel, QgsMapLayerProxyModel, QgsMessageBar

from cartogram_dialog import CartogramDialog
from cartogram_worker import CartogramWorker

import math
import os.path
import resources_rc


class Cartogram:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        # save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            '{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # declare instance attributes
        self.action = None
        self.menu = self.tr(u'&Cartogram')

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # create action to display the settings dialog
        self.action = QAction(
            QIcon(':/plugins/cartogram/assets/icon.png'),
            self.tr(u'Create cartogram...'),
            self.iface.mainWindow())

        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu(self.menu, self.action)

    def unload(self):
        """Removes the plugin menu item and icon from the QGIS GUI."""
        self.iface.removePluginVectorMenu('&Cartogram', self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        """Run method that performs all the real work."""
        # create the dialog (after translation) and keep reference
        self.dialog = CartogramDialog()

        # make sure we have at least one vector layer to work on
        count = self.count_vector_layers()
        if count == 0:
            message = self.tr(u'You need at least one vector layer to create a \
                cartogram.')
            self.iface.messageBar().pushMessage(
                'Error', message, level=QgsMessageBar.CRITICAL, duration=5)
            return False

        # we are only interested in polygon layers and numeric fields
        self.dialog.sourceLayerCombo.setFilters(
            QgsMapLayerProxyModel.PolygonLayer)
        self.dialog.sourceFieldCombo.setFilters(QgsFieldProxyModel.Numeric)

        # select the first layer in the list and notify the field combobox
        self.dialog.sourceLayerCombo.setCurrentIndex(0)
        currentLayer = self.dialog.sourceLayerCombo.currentLayer()
        self.dialog.sourceLayerCombo.layerChanged.emit(currentLayer)

        # connect some odds and ends
        self.dialog.buttonBox.accepted.connect(self.validate)

        # show the dialog
        self.dialog.show()
        result = self.dialog.exec_()
        if result == QDialog.Rejected:
            return False

        input_layer_name = self.dialog.sourceLayerCombo.currentText()
        input_layer = self.get_vector_layer_by_name(input_layer_name)
        input_field = self.dialog.sourceFieldCombo.currentText()
        iterations = self.dialog.iterationsSpinBox.value()

        memory_layer = self.create_memory_layer(input_layer)
        memory_layer_data_provider = memory_layer.dataProvider()

        self.worker_start(memory_layer, input_field, iterations)

    def worker_start(self, layer, field_name, iterations):
        """Start a worker instance on a background thread."""
        worker = CartogramWorker(layer, field_name, iterations)

        message_bar = self.iface.messageBar().createMessage('')

        label = QLabel('Creating cartogram...')
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        progress_bar = QProgressBar()
        progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        progress_bar.setMaximum(iterations * layer.featureCount())

        cancel_button = QPushButton()
        cancel_button.setText(self.tr(u'Cancel'))
        cancel_button.clicked.connect(worker.kill)

        message_bar.layout().addWidget(label)
        message_bar.layout().addWidget(progress_bar)
        message_bar.layout().addWidget(cancel_button)

        self.iface.messageBar().pushWidget(message_bar,
            self.iface.messageBar().INFO)
        self.message_bar = message_bar

        # start the worker in a new thread
        thread = QThread()
        worker.moveToThread(thread)

        # connect some odds and ends
        worker.finished.connect(self.worker_finished)
        worker.error.connect(self.worker_error)
        worker.progress.connect(progress_bar.setValue)
        thread.started.connect(worker.run)

        thread.start()

        self.thread = thread
        self.worker = worker

    def worker_finished(self, layer):
        """Clean up after the worker and the thread."""

        self.worker.deleteLater()
        self.thread.quit()
        self.thread.wait()
        self.thread.deleteLater()

        self.iface.messageBar().popWidget(self.message_bar)

        if layer is not None:
            QgsMapLayerRegistry.instance().addMapLayer(layer)
        else:
            message = 'Cartogram creation cancelled by user.'
            self.iface.messageBar().pushMessage(message,
                level=QgsMessageBar.INFO, duration=3)

    def worker_error(self, e, exception_string):
        message = 'Worker thread exception:\n'.format(exception_string)
        QgsMessageLog.logMessage(message, level=QgsMessageLog.CRITICAL)

    def validate(self):
        """Make sure that all fields have valid values."""
        message = ''
        if not self.dialog.sourceLayerCombo.currentText():
            message += self.tr(u'Please select an input layer.\n')
        if not self.dialog.sourceFieldCombo.currentText():
            message += self.tr(u'Please select an area field.\n')

        if message:
            QMessageBox.warning(self.dialog, 'Cartogram', message)
        else:
            self.dialog.accept()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Cartogram', message)

    def get_vector_layer_by_name(self, layer_name):
        """Retrieve a layer from the registry by name."""
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for name, layer in layerMap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer \
                    and layer.name() == layer_name:
                if layer.isValid():
                    return layer
                else:
                    return None

    def count_vector_layers(self):
        """Count the number of vector layers on the canvas."""
        layermap = QgsMapLayerRegistry.instance().mapLayers()

        count = 0
        for name, layer in layermap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer:
                if layer.geometryType() == QGis.Polygon:
                    count += 1

        return count

    def create_memory_layer(self, layer):
        """Create an in-memory copy of an existing vector layer."""

        data_provider = layer.dataProvider()

        # create the layer path defining geometry type and reference system
        geometry_type = QGis.vectorGeometryType(layer.geometryType())
        crs_id = layer.crs().authid()
        path = geometry_type + '?crs=' + crs_id + '&index=yes'

        # create the memory layer and get a reference to the data provider
        memory_layer = QgsVectorLayer(path, 'cartogram', 'memory')
        memory_layer_data_provider = memory_layer.dataProvider()

        # copy all attributes from the source layer to the memory layer
        memory_layer.startEditing()
        memory_layer_data_provider.addAttributes(
            data_provider.fields().toList())
        memory_layer.commitChanges()

        # copy all features from the source layer to the memory layer
        for feature in data_provider.getFeatures():
            memory_layer_data_provider.addFeatures([feature])

        return memory_layer
