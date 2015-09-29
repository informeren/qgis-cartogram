from PyQt4.QtCore import pyqtSignal, QObject
from qgis.core import QgsDistanceArea, QgsGeometry, QgsMessageLog, QgsPoint

from cartogram_feature import CartogramFeature

import math
import traceback


class CartogramWorker(QObject):
    """Background worker which actually creates the cartogram."""

    finished = pyqtSignal(object)
    error = pyqtSignal(Exception, basestring)
    progress = pyqtSignal(float)

    def __init__(self, layer, field_name, iterations):
        """Constructor."""
        QObject.__init__(self)

        self.layer = layer
        self.field_name = field_name
        self.iterations = iterations

        self.killed = False

    def run(self):
        ret = None

        try:
            feature_count = self.layer.featureCount()

            step = self.get_step()
            steps = 0

            for i in range(self.iterations):
                (meta_features,
                    force_reduction_factor) = self.get_reduction_factor(
                    self.layer, self.field_name)

                for feature in self.layer.getFeatures():
                    if self.killed is True:
                        break

                    old_geometry = feature.geometry()
                    new_geometry = self.transform(meta_features,
                        force_reduction_factor, old_geometry)

                    self.layer.dataProvider().changeGeometryValues({
                        feature.id() : new_geometry})

                    steps += 1
                    if step == 0 or steps % step == 0:
                        self.progress.emit(steps / float(feature_count) * 100)

            if self.killed is False:
                self.progress.emit(100)
                ret = self.layer
        except Exception, e:
            self.error.emit(e, traceback.format_exc())

        self.finished.emit(ret)

    def kill(self):
        self.killed = True

    def get_reduction_factor(self, layer, field):
        """Calculate the reduction factor."""
        data_provider = layer.dataProvider()
        meta_features = []

        total_area = 0.0
        total_value = 0.0

        for feature in data_provider.getFeatures():
            meta_feature = CartogramFeature()

            geometry = QgsGeometry(feature.geometry())

            area = QgsDistanceArea().measure(geometry)
            total_area += area

            feature_value = feature.attribute(field)
            if feature_value is None:
                total_value += 0
            else:
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

    def transform(self, meta_features, force_reduction_factor, geometry):
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

    def transform_polygon(self, polygon, meta_features,
        force_reduction_factor):
        """Transform the geometry of a single polygon."""

        new_line = []
        new_polygon = []

        for line in polygon:
            for point in line:
                x = x0 = point.x()
                y = y0 = point.y()

                # compute the influence of all shapes on this point
                for feature in meta_features:
                    cx = feature.center_x
                    cy = feature.center_y
                    distance = math.sqrt((x0 - cx) ** 2 + (y0 - cy) ** 2)

                    if (distance > feature.radius):
                        # calculate the force exerted on points far away from
                        # the centroid of this polygon
                        force = feature.mass * feature.radius / distance
                    else:
                        # calculate the force exerted on points close to the
                        # centroid of this polygon
                        xF = distance / feature.radius
                        # distance ** 2 / feature.radius ** 2 instead of xF
                        force = feature.mass * (xF ** 2) * (4 - (3 * xF))
                    force = force * force_reduction_factor / distance
                    x = (x0 - cx) * force + x
                    y = (y0 - cy) * force + y
                new_line.append(QgsPoint(x, y))
            new_polygon.append(new_line)
            new_line = []

        return new_polygon

    def get_step(self):
        """Determine how often the progress bar should be updated."""

        feature_count = self.layer.featureCount()

        # update the progress bar at each .1% increment
        step = feature_count // 1000

        # because we use modulo to determine if we should emit the progress
        # signal, the step needs to be greater than 1
        if step < 2:
            step = 2

        return step
