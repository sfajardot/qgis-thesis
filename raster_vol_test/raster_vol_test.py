# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RasterTester
                                 A QGIS plugin
 Raster Volume Tester
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-08-30
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Sebastian
        email                : mail@mail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# ADD SELECTED BOUNDING BOX
# PlugIn in a second label to customize final report

import os
import sys

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import  Qgis,  QgsMessageLog, QgsMapLayerProxyModel, QgsFieldProxyModel

from PyQt5.QtWidgets import QFileDialog, QMessageBox

import csv

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .raster_vol_test_dialog import RasterTesterDialog
#Import layout functions created by developer
from .functions import *


class RasterTester:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'RasterTester_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Raster Tester')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('RasterTester', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/raster_vol_test/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Vol Tester'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """
        Remove the plugin's menu item and icon from the QGIS interface.

        This function is used when the plugin is unloaded or deactivated. It removes the plugin-related actions 
        (menu items and toolbar icons) from QGIS, ensuring a clean removal of the plugin UI elements.

        Args:
        - None.

        Returns:
        - None, but removes the plugin's actions from the QGIS interface.
        """
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Raster Tester'),
                action)
            self.iface.removeToolBarIcon(action)

    def enable_button(self, chkbox, enblBtn):
        """
        Enable or disable a button based on the state of a checkbox.

        This function checks if a specified checkbox is selected (`checked`).
        If the checkbox is checked, it enables the associated button.
        If the checkbox is unchecked, it disables the button.

        Args:
        - chkbox: The checkbox that controls the button's state.
        - enblBtn: The button to be enabled or disabled based on the checkbox state.

        Returns:
        - None, but enables or disables the button visually.
        """
        for btn in enblBtn:
            if chkbox.isChecked():
                btn.setEnabled(True)
                btn.repaint()
            else:
                btn.setDisabled(True)
                btn.repaint()

    def enable_symbology(self, symType, enable_grad, enable_vfm):
        """
        Enable or disable buttons based on the state of the symbology chosen.

        This function checks if a specified checkbox is selected (`checked`).
        If the checkbox is checked, it enables the associated button.
        If the checkbox is unchecked, it disables the button.

        Args:
        - symType: The type of symbology given by a combo Box.
        - enblBtn: The button to be enabled or disabled based on the checkbox state.

        Returns:
        - None, but enables or disables the button visually.
        """
        for wdgt in enable_grad:
            if symType.currentText() == 'Graduated':
                wdgt.setEnabled(True)
            elif symType.currentText() == 'Vector Field Marker':
                wdgt.setEnabled(False)
        for wdgt in enable_vfm:
            if symType.currentText() == 'Graduated':
                wdgt.setEnabled(False)
            elif symType.currentText() == 'Vector Field Marker':
                wdgt.setEnabled(True)

    def enable_exceptions(self, chkBox,  symType, enable_grad, enable_vfm):
        if chkBox.isChecked():
            self.enable_symbology(symType, enable_grad, enable_vfm)

    def enable_weight(self, cmbInterpolationType):
        if cmbInterpolationType.currentText() == 'IDW':
            self.dlg.spbWeight.setEnabled(True)
        else:
            self.dlg.spbWeight.setEnabled(False)



    def select_output_file(self, default_name, file_filter, line_edit):
        """
        Open a file dialog to select a save path for an output file.

        This function prompts the user to select the location and filename for saving an output file (e.g., a raster file).
        The file path chosen by the user is displayed in the specified line edit widget.

        Args:
        - default_name: The default name or directory path for the output file.
        - file_filter: The file type filter (e.g., 'GTiff (*.tif)') for the save dialog.
        - line_edit: The QLineEdit widget to display the selected file path.

        Returns:
        - None, but updates the QLineEdit with the selected file path.
        """

        filename, _filter = QFileDialog.getSaveFileName(
            self.dlg, "Select output filename and destination", default_name, file_filter)
        if filename:
            line_edit.setText(filename)

    def select_input_file(self, line_edit):
        """
        Open a file dialog to select an image file (JPG or PNG) for input.

        This function prompts the user to select an image file (JPG or PNG), such as a logo, for input. 
        The selected file path is displayed in the specified line edit widget.

        Args:
        - line_edit: The QLineEdit widget to display the selected image file path.

        Returns:
        - None, but updates the QLineEdit with the selected file path.
        """
        file_filter = 'Image Files (*.jpg, *png)'
        filename, _filter = QFileDialog.getOpenFileName(
            self.dlg, "Select Image File","", file_filter)
        if filename:
            line_edit.setText(filename)
    
    def processing_tab(self):
        """
        Process the elevation change task when the corresponding button is pressed.

        This function logs a message when the 'Processing' button is pressed. It then calls the `elevation_change` 
        function, which calculates the difference between two raster layers, and closes the dialog after processing.

        Args:
        - None, but relies on UI inputs for raster layers, bounding box options, and output paths.

        Returns:
        - None, but performs elevation change processing and closes the dialog.
        """

        QgsMessageLog.logMessage('Processing button pressed', 'vol test', Qgis.Info)
        elevation_change(self, self.dlg.lnOutput, self.dlg.cmbOld, self.dlg.cmbNew,
                         self.dlg.chkBB, self.dlg.cmbBB, self.dlg.chkStats, self.dlg.lnOutputStats,
                         self.dlg.chkChangeType, self.dlg.spbTimeChange)
        self.dlg.close()


    def monography_tab(self):
        """
        Process the monograph creation task when the corresponding button is pressed and if checked, processes the graduated map layout when the corresponding button is pressed.

        This function logs a message when the 'Monography' button is pressed. It calls the `create_monograph` function,
        which generates a monograph layout with the selected feature, descriptions, and images, and then closes the dialog.
        If the checkbox for point symbology is checked it also logs a message when the 'Layout' button is pressed. It then 
        calls the `symbolized_map` function, which creates a graduated map layout with the selected symbology 
        and field values, and closes the dialog.

        Args:
        - None, but relies on UI inputs for the point layer, feature, target color, description, GNSS info, and image paths.

        Returns:
        - None, but performs monograph creation and closes the dialog.
        """
        QgsMessageLog.logMessage('Monography button pressed', 'vol test', Qgis.Info)
        create_monograph(self, self.dlg.cmbMonoPoints, self.dlg.cmbMonoFeat, self.dlg.txtTrgClr,
                         self.dlg.txtTrgDscr, self.dlg.txtGnss, self.dlg.lnLogo, self.dlg.lnPhoto_1,
                         self.dlg.lnPhoto_2, self.dlg.lnInst, self.dlg.cmbFieldLabel, self.dlg.cmbFieldSurvey,
                         self.dlg.spbNumSrvy, self.dlg.cmbHeight)

        self.dlg.close()

    def interpolation_tab(self):
        QgsMessageLog.logMessage('Interpolation button pressed', 'vol test', Qgis.Info)
        if self.dlg.chkInterpolation.isChecked():
            interpolator(self, self.dlg.cmbInterpolationLayer, self.dlg.cmbInterpolationField,
                        self.dlg.cmbInterpolationType, self.dlg.lnOutputInter, self.dlg.spbResolution,
                        self.dlg.spbWeight, self.dlg.lnInterFilter)
        if self.dlg.chkSymbology.isChecked():
            symbolized_map(self, self.dlg.cmbInterpolationLayer, self.dlg.cmbFieldValue, self.dlg.cmbGradMeth, self.dlg.spbNumClass, self.dlg.cmbSymType, self.dlg.cmbXMag, self.dlg.cmbYMag, self.dlg.spbScale, self.dlg.lnInterFilter)
        self.dlg.close()
                
    def populate_fields(self, cmbPopulator, cmbPopulated, QgsFilter = None):
        """
        Populate a combo box with data from a selected layer, optionally applying a filter.

        This function sets the layer for the `cmbPopulated` combo box based on the currently selected layer in `cmbPopulator`.
        Optionally, it applies a filter (`QgsFilter`) to restrict the fields shown in the populated combo box.

        Args:
        - cmbPopulator: The combo box that holds the currently selected layer.
        - cmbPopulated: The combo box to be populated with fields from the selected layer.
        - QgsFilter (optional): A filter to restrict the fields, such as `QgsFieldProxyModel.Numeric` for numeric fields.

        Returns:
        - None, but updates the `cmbPopulated` combo box with fields from the selected layer.
        """
        cmbPopulated.setLayer(cmbPopulator.currentLayer())
        if QgsFilter:
            cmbPopulated.setFilters(QgsFilter)

    def populate_list(self, cmbPopulator, cmbPopulated, cmbAttributeField):
        # Get the layer and field
        layer = cmbPopulator.currentLayer()
        field_name = cmbAttributeField.currentField()

        cmbPopulated.setLayer(layer)
        cmbPopulated.setDisplayExpression(field_name)

    def unique_field_values(self, cmbLayerPopulator, cmbFieldPopulator, cmbPopulated):
        layer = cmbLayerPopulator.currentLayer()
        field_name = cmbFieldPopulator.currentField()
        cmbPopulated.clear()
        unique_values = set()
        if layer:
            for feature in layer.getFeatures():
                value = feature[field_name]
                if value is not None:
                    unique_values.add(str(value))
        unique_values = sorted(unique_values)
        cmbPopulated.addItems(unique_values)



    def close_dialog(self):
        """
        Close the dialog window.

        This function simply closes the dialog window when called.

        Args:
        - None.

        Returns:
        - None, but closes the dialog window.
        """
        self.dlg.close()

    def clear_data(self, lnWdgts =[], tblWdgts=[]):
        """
        Clear the contents of specified line edit and table widgets.

        This function iterates through a list of line edit widgets (`lnWdgts`) and clears their contents.
        It also iterates through a list of table widgets (`tblWdgts`) and clears all the data in their contents.

        Args:
        - lnWdgts: A list of line edit widgets (QLineEdit) to be cleared.
        - tblWdgts: A list of table widgets (QTableWidget) to be cleared.

        Returns:
        - None, but clears the content of the specified line and table widgets.
        """
        for lnWdgt in lnWdgts:
            lnWdgt.clear()
        for tblWdgt in tblWdgts:
            tblWdgt.clearContents()

    def clear_filters(self, filter_box, layer):
        filter_box.setExpression('')
        if layer:
            layer.setSubsetString('')

    def connect_filter(self, cmbLayer, lnFilter, cmbField = False):
        lnFilter.setLayer(cmbLayer.currentLayer())
        if cmbField:
            lnFilter.setField(cmbField.currentField())



    def run(self):
        """Run method to initialize the plugin."""
        if self.first_start:
            self.first_start = False
            self.dlg = RasterTesterDialog()

            # File dialog connections
            self.dlg.btnOutput.clicked.connect(lambda: self.select_output_file(
                'ElevationChange', 'GeoTIFF(*.tif)', self.dlg.lnOutput))
            self.dlg.btnOutputStats.clicked.connect(lambda: self.select_output_file(
                'RasterStatistics', 'csv(*.csv)', self.dlg.lnOutputStats))
            self.dlg.btnOutputInter.clicked.connect(lambda: self.select_output_file(
                'Interpolation', 'GeoTiff(*.tif)', self.dlg.lnOutputInter))
            self.dlg.btnLogo.clicked.connect(lambda: self.select_input_file(
                self.dlg.lnLogo))
            self.dlg.btnPhoto_1.clicked.connect(lambda: self.select_input_file(
                self.dlg.lnPhoto_1))
            self.dlg.btnPhoto_2.clicked.connect(lambda: self.select_input_file(
                self.dlg.lnPhoto_2))

            # Processing
            self.dlg.btnProcess.accepted.connect(self.processing_tab)
            self.dlg.btnProcess.rejected.connect(self.close_dialog)
            self.dlg.btnProcess.accepted.connect(lambda: self.clear_data([self.dlg.lnOutput, self.dlg.lnOutputStats], []))
            self.dlg.btnProcess.rejected.connect(lambda: self.clear_data([self.dlg.lnOutput, self.dlg.lnOutputStats], []))

            # Monography actions
            self.dlg.btnMono.accepted.connect(self.monography_tab)
            self.dlg.btnMono.rejected.connect(self.close_dialog)
            self.dlg.btnMono.accepted.connect(lambda: self.clear_data([self.dlg.lnInst, self.dlg.lnLogo,
                                                                              self.dlg.lnPhoto_1, self.dlg.lnPhoto_2,
                                                                              self.dlg.txtGnss, self.dlg.txtTrgClr, self.dlg.txtTrgDscr]))
            self.dlg.btnMono.rejected.connect(lambda: self.clear_data([self.dlg.lnInst, self.dlg.lnLogo,
                                                                              self.dlg.lnPhoto_1, self.dlg.lnPhoto_2,
                                                                              self.dlg.txtGnss, self.dlg.txtTrgClr, self.dlg.txtTrgDscr]))
            self.dlg.btnClearAllMono.clicked.connect(lambda: self.clear_data([self.dlg.lnInst, self.dlg.lnLogo,
                                                                              self.dlg.lnPhoto_1, self.dlg.lnPhoto_2,
                                                                              self.dlg.txtGnss, self.dlg.txtTrgClr, self.dlg.txtTrgDscr]))

            #Interpolation actions
            self.dlg.btnInterpolation.accepted.connect(self.interpolation_tab)
            self.dlg.btnInterpolation.rejected.connect(self.close_dialog)
            

            # Populate fields for Layout Tabs
            self.dlg.cmbInterpolationLayer.layerChanged.connect(lambda: self.populate_fields(self.dlg.cmbInterpolationLayer, self.dlg.cmbFieldValue,
                                                                                        QgsFieldProxyModel.Numeric))
            self.dlg.cmbInterpolationLayer.layerChanged.connect(lambda: self.populate_fields(self.dlg.cmbInterpolationLayer, self.dlg.cmbXMag,
                                                                                        QgsFieldProxyModel.Numeric))
            self.dlg.cmbInterpolationLayer.layerChanged.connect(lambda: self.populate_fields(self.dlg.cmbInterpolationLayer, self.dlg.cmbYMag,
                                                                                        QgsFieldProxyModel.Numeric))
            #Populate fields for survey and label name
            self.dlg.cmbMonoPoints.layerChanged.connect(lambda: self.populate_fields(self.dlg.cmbMonoPoints, self.dlg.cmbFieldLabel))
            self.dlg.cmbMonoPoints.layerChanged.connect(lambda: self.populate_fields(self.dlg.cmbMonoPoints, self.dlg.cmbFieldSurvey,  
                                                                                     QgsFilter=QgsFieldProxyModel.Date))
            self.dlg.cmbMonoPoints.layerChanged.connect(lambda: self.populate_fields(self.dlg.cmbMonoPoints, self.dlg.cmbHeight))

            #populate feature points for monography
            self.dlg.cmbFieldLabel.fieldChanged.connect(lambda: self.unique_field_values(self.dlg.cmbMonoPoints, self.dlg.cmbFieldLabel, self.dlg.cmbMonoFeat))
            self.dlg.cmbMonoPoints.layerChanged.connect(lambda: self.unique_field_values(self.dlg.cmbMonoPoints, self.dlg.cmbFieldLabel, self.dlg.cmbMonoFeat))

            #populate fields for interpolation combobox
            self.dlg.cmbInterpolationLayer.layerChanged.connect(lambda: self.populate_fields(self.dlg.cmbInterpolationLayer, self.dlg.cmbInterpolationField,
                                                                                        QgsFieldProxyModel.Numeric))

            #Connect filter if layer or field is changed
            self.dlg.cmbInterpolationLayer.layerChanged.connect(lambda: self.connect_filter(self.dlg.cmbInterpolationLayer, self.dlg.lnInterFilter))

            # Set filters for combo boxes
            self.dlg.cmbOld.setFilters(QgsMapLayerProxyModel.RasterLayer)
            self.dlg.cmbNew.setFilters(QgsMapLayerProxyModel.RasterLayer)
            self.dlg.cmbBB.setFilters(QgsMapLayerProxyModel.PolygonLayer)
            self.dlg.cmbMonoPoints.setFilters(QgsMapLayerProxyModel.PointLayer)
            self.dlg.cmbInterpolationLayer.setFilters(QgsMapLayerProxyModel.PointLayer)


            # Initialize field and feature values
            self.populate_fields(self.dlg.cmbInterpolationLayer, self.dlg.cmbFieldValue, QgsFieldProxyModel.Numeric)
            self.populate_fields(self.dlg.cmbInterpolationLayer, self.dlg.cmbXMag, QgsFieldProxyModel.Numeric)
            self.populate_fields(self.dlg.cmbInterpolationLayer, self.dlg.cmbYMag, QgsFieldProxyModel.Numeric)
            self.populate_fields(self.dlg.cmbMonoPoints, self.dlg.cmbFieldLabel)
            self.populate_fields(self.dlg.cmbMonoPoints, self.dlg.cmbFieldSurvey, QgsFilter=QgsFieldProxyModel.Date)

            self.unique_field_values(self.dlg.cmbMonoPoints, self.dlg.cmbFieldLabel, self.dlg.cmbMonoFeat)
            self.populate_fields(self.dlg.cmbMonoPoints, self.dlg.cmbHeight)
            self.populate_fields(self.dlg.cmbInterpolationLayer, self.dlg.cmbInterpolationField, QgsFieldProxyModel.Numeric)
            self.enable_symbology(self.dlg.cmbSymType, [self.dlg.cmbFieldValue, self.dlg.cmbGradMeth, self.dlg.spbNumClass],
                                   [self.dlg.cmbXMag, self.dlg.cmbYMag, self.dlg.spbScale])
            self.enable_weight(self.dlg.cmbInterpolationType)
            self.connect_filter(self.dlg.cmbInterpolationLayer, self.dlg.lnInterFilter)
            
             

        # show the dialog
        #Do the dynamic connections for buttons that enbale/disable functions
        self.dlg.chkBB.clicked.connect(lambda: self.enable_button(self.dlg.chkBB, [self.dlg.cmbBB] ))
        self.dlg.chkStats.clicked.connect(lambda: self.enable_button(self.dlg.chkStats, [self.dlg.lnOutputStats, self.dlg.btnOutputStats]))
        self.dlg.cmbSymType.currentTextChanged.connect(lambda: self.enable_symbology(self.dlg.cmbSymType, 
                                                                                     [self.dlg.cmbFieldValue, self.dlg.cmbGradMeth, self.dlg.spbNumClass],
                                                                                       [self.dlg.cmbXMag, self.dlg.cmbYMag, self.dlg.spbScale]))
        self.dlg.chkSymbology.clicked.connect(lambda: self.enable_button(self.dlg.chkSymbology, [self.dlg.cmbFieldValue, self.dlg.cmbGradMeth, self.dlg.spbNumClass,
                                                                                             self.dlg.cmbXMag, self.dlg.cmbYMag, self.dlg.spbScale,
                                                                                             self.dlg.cmbSymType]))
        self.dlg.chkSymbology.clicked.connect(lambda: self.enable_exceptions(self.dlg.chkSymbology,  self.dlg.cmbSymType,
                                                                             [self.dlg.cmbFieldValue, self.dlg.cmbGradMeth, self.dlg.spbNumClass],
                                                                               [self.dlg.cmbXMag, self.dlg.cmbYMag, self.dlg.spbScale]))
        self.dlg.chkInterpolation.clicked.connect(lambda: self.enable_button(self.dlg.chkInterpolation, [self.dlg.cmbInterpolationType, self.dlg.spbWeight, 
                                                                                                          self.dlg.spbResolution, self.dlg.lnOutputInter, self.dlg.btnOutputInter ]))
        self.dlg.cmbInterpolationType.currentTextChanged.connect(lambda: self.enable_weight(self.dlg.cmbInterpolationType))
        self.dlg.btnClearFilter.clicked.connect(lambda: self.clear_filters(self.dlg.lnInterFilter, self.dlg.cmbInterpolationLayer.currentLayer()))
        
        #Show the dialogue
        self.dlg.show()

        result = self.dlg.exec_()
        if result:
            if self.dlg.btnProcess.accepted == True:
                self.processing_tab
            if self.dlg.btnMono.accepted == True:
                self.monography_tab
            if self.dlg.btnInterpolation.accepted == True:
                self.interpolation_tab