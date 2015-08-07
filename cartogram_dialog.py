# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'cartogram_dialog.ui'
#
# Created: Thu Aug  6 11:36:26 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_CartogramDialog(object):
    def setupUi(self, CartogramDialog):
        CartogramDialog.setObjectName(_fromUtf8("CartogramDialog"))
        CartogramDialog.resize(280, 190)
        CartogramDialog.setModal(True)
        self.formLayout = QtGui.QFormLayout(CartogramDialog)
        self.formLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.sourceLayerLabel = QtGui.QLabel(CartogramDialog)
        self.sourceLayerLabel.setObjectName(_fromUtf8("sourceLayerLabel"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.sourceLayerLabel)
        self.sourceLayerCombo = gui.QgsMapLayerComboBox(CartogramDialog)
        self.sourceLayerCombo.setObjectName(_fromUtf8("sourceLayerCombo"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.SpanningRole, self.sourceLayerCombo)
        self.sourceFieldLabel = QtGui.QLabel(CartogramDialog)
        self.sourceFieldLabel.setObjectName(_fromUtf8("sourceFieldLabel"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.sourceFieldLabel)
        self.sourceFieldCombo = gui.QgsFieldComboBox(CartogramDialog)
        self.sourceFieldCombo.setObjectName(_fromUtf8("sourceFieldCombo"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.SpanningRole, self.sourceFieldCombo)
        self.iterationsLabel = QtGui.QLabel(CartogramDialog)
        self.iterationsLabel.setObjectName(_fromUtf8("iterationsLabel"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.iterationsLabel)
        self.iterationsSpinBox = QtGui.QSpinBox(CartogramDialog)
        self.iterationsSpinBox.setMinimum(1)
        self.iterationsSpinBox.setProperty("value", 5)
        self.iterationsSpinBox.setObjectName(_fromUtf8("iterationsSpinBox"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.iterationsSpinBox)
        self.buttonBox = QtGui.QDialogButtonBox(CartogramDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.formLayout.setWidget(5, QtGui.QFormLayout.SpanningRole, self.buttonBox)

        self.retranslateUi(CartogramDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CartogramDialog.reject)
        QtCore.QObject.connect(self.sourceLayerCombo, QtCore.SIGNAL(_fromUtf8("layerChanged(QgsMapLayer*)")), self.sourceFieldCombo.setLayer)
        QtCore.QMetaObject.connectSlotsByName(CartogramDialog)
        CartogramDialog.setTabOrder(self.sourceLayerCombo, self.sourceFieldCombo)
        CartogramDialog.setTabOrder(self.sourceFieldCombo, self.iterationsSpinBox)
        CartogramDialog.setTabOrder(self.iterationsSpinBox, self.buttonBox)

    def retranslateUi(self, CartogramDialog):
        CartogramDialog.setWindowTitle(_translate("CartogramDialog", "Cartogram", None))
        self.sourceLayerLabel.setText(_translate("CartogramDialog", "Input layer:", None))
        self.sourceFieldLabel.setText(_translate("CartogramDialog", "Area field:", None))
        self.iterationsLabel.setText(_translate("CartogramDialog", "Number of iterations to perform:", None))

from qgis import gui

class CartogramDialog(QtGui.QDialog, Ui_CartogramDialog):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QDialog.__init__(self, parent, f)

        self.setupUi(self)

