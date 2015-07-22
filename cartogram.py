from PyQt4.QtCore import Qt, QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import (QAction, QDialog, QFileDialog, QIcon, QMessageBox,
    QProgressBar)
from qgis.core import (QGis, QgsDistanceArea, QgsGeometry, QgsMapLayer,
    QgsMapLayerRegistry, QgsMessageLog, QgsPoint, QgsVectorFileWriter,
    QgsVectorLayer)
from qgis.gui import QgsFieldProxyModel, QgsMapLayerProxyModel, QgsMessageBar
from cartogram_dialog import CartogramDialog

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
            QIcon(':/plugins/cartogram/icon.png'),
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
                'Error', message, level=QgsMessageBar.CRITICAL, duration=10)
            return False

        # prepare the progress bar
        self.progress = QProgressBar()
        self.progress.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.progress_msg_bar = self.iface.messageBar().createMessage(
            'Creating cartogram...')
        self.progress_msg_bar.layout().addWidget(self.progress)

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

        self.cartogram(input_layer, input_field, iterations)

    def cartogram(self, layer, field_name, iterations):
        crs = layer.crs()
        data_provider = layer.dataProvider()

        # initialize the progress bar
        feature_count = data_provider.featureCount()
        self.progress.setMaximum(iterations * feature_count)
        self.iface.messageBar().pushWidget(self.progress_msg_bar,
            self.iface.messageBar().INFO)

        memory_layer = self.create_memory_layer(layer)
        memory_layer_data_provider = memory_layer.dataProvider()

        steps = 0
        for i in range(iterations):
            (meta_features,
                force_reduction_factor) = self.get_reduction_factor(
                memory_layer, field_name)

            # memory_layer.startEditing()

            for feature in memory_layer_data_provider.getFeatures():
                steps += 1
                self.progress.setValue(steps)
                old_geometry = feature.geometry()
                new_geometry = self.transform(meta_features,
                    force_reduction_factor, old_geometry)

                memory_layer_data_provider.changeGeometryValues({
                    feature.id() : new_geometry})

            # memory_layer.commitChanges()

        self.iface.messageBar().clearWidgets()

        QgsMapLayerRegistry.instance().addMapLayer(memory_layer)

    def get_reduction_factor(self, layer, field):
        """Calculate the reduction factor."""
        data_provider = layer.dataProvider()
        meta_features = []

        total_area = 0.0
        total_value = 0.0

        for feature in data_provider.getFeatures():
            meta_feature = MetaFeature()

            geometry = QgsGeometry(feature.geometry())

            area = QgsDistanceArea().measure(geometry)
            total_area += area

            feature_value = feature.attribute(field)
            total_value += feature_value

            meta_feature.area = area
            meta_feature.value = feature_value

            centroid = geometry.centroid()
            (cx, cy) = centroid.asPoint().x(), centroid.asPoint().y()
            meta_feature.center_x = cx
            meta_feature.center_y = cy

            meta_features.append(meta_feature)

        fraction = total_area / total_value

        total_size_error = 0

        for meta_feature in meta_features:
            polygon_value = meta_feature.value
            polygon_area = meta_feature.area

            if polygon_area < 0:
                polygon_area = 0

            # this is our 'desired' area...
            desired_area = polygon_value * fraction

            # calculate radius, a zero area is zero radius
            radius = math.sqrt(polygon_area / math.pi)
            meta_feature.radius = radius

            if desired_area / math.pi > 0:
                mass = math.sqrt(desired_area / math.pi) - radius
                meta_feature.mass = mass
            else:
                meta_feature.mass = 0

            size_error = max(polygon_area, desired_area) / \
                min(polygon_area, desired_area)

            total_size_error += size_error

        average_error = total_size_error / len(meta_features)
        force_reduction_factor = 1 / (average_error + 1)

        return (meta_features, force_reduction_factor)

    def transform_polygon(self, polygon, meta_features,
        force_reduction_factor):
        """Transform the geometry of a single polygon."""
        new_line = []
        new_polygon = []

        for line in polygon:
            for point in line:
                x = x0 = point.x()
                y = y0 = point.y()
                # Compute the influence of all shapes on this point
                for feature in meta_features:
                    cx = feature.center_x
                    cy = feature.center_y
                    distance = math.sqrt((x0 - cx) ** 2 + (y0 - cy) ** 2)

                    if (distance > feature.radius):
                        # Calculate the force on verteces far away
                        # from the centroid of this feature
                        Fij = feature.mass * feature.radius / distance
                    else:
                        # Calculate the force on verteces far away
                        # from the centroid of this feature
                        xF = distance / feature.radius
                        Fij = feature.mass * (xF ** 2) * (4 - (3 * xF))
                    Fij = Fij * force_reduction_factor / distance
                    x = (x0 - cx) * Fij + x
                    y = (y0 - cy) * Fij + y
                new_line.append(QgsPoint(x, y))
            new_polygon.append(new_line)
            new_line = []

        return new_polygon

    def transform(self, meta_features,
        force_reduction_factor, geometry):
        """Transform the geometry based on the force reduction factor."""

        if geometry.isMultipart():
            geometries = []
            for polygon in geometry.asMultiPolygon():
                new_polygon = self.transform_polygon(polygon, meta_features,
                    force_reduction_factor)
                geometries.append(new_polygon)
            return QgsGeometry.fromMultiPolygon(geometries)
        else:
            polygon = geometry.asPolygon()
            new_polygon = self.transform_polygon(polygon, meta_features,
                force_reduction_factor)
            return QgsGeometry.fromPolygon(new_polygon)

        return geometry

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
        memory_layer_data_provider.addAttributes(data_provider.fields().toList())
        memory_layer.commitChanges()

        # copy all features from the source layer to the memory layer
        for feature in data_provider.getFeatures():
            memory_layer_data_provider.addFeatures([feature])

        return memory_layer


class MetaFeature(object):
    """Stores various calculated values for each feature."""

    def __init__(self):
        self.center_x = -1
        self.center_y = -1
        self.value = -1
        self.area = -1
        self.mass = -1
        self.radius = -1
