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
        copyright            : (C) 2024 by Simona
        email                : lacacariza@mail.com
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
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
from qgis.utils import iface

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

    def enable_bounding_box(self):
        if self.dlg.chkBB.isChecked():
            self.dlg.cmbBB.setEnabled(True)
            self.dlg.cmbBB.repaint()
        else:
            self.dlg.cmbBB.setDisabled(True)
            self.dlg.cmbBB.repaint()
    def enable_stats_box(self):
        if self.dlg.chkStats.isChecked():
            self.dlg.lnOutputStats.setEnabled(True)
            self.dlg.lnOutputStats.repaint()
            self.dlg.btnOutputStats.setEnabled(True)
            self.dlg.btnOutputStats.repaint()
        else:
            self.dlg.lnOutputStats.setDisabled(True)
            self.dlg.lnOutputStats.repaint()
            self.dlg.btnOutputStats.setDisabled(True)
            self.dlg.btnOutputStats.repaint()
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Raster Tester'),
                action)
            self.iface.removeToolBarIcon(action)

    def select_output_file(self):  
        
        FileName = 'ElevationChange'
        filename, _filter = QFileDialog.getSaveFileName(  
            self.dlg, "Select output filename and destination",FileName, 'GeoTIFF(*.tif)')  
        self.dlg.lnOutput.setText(filename)  
    def select_output_file_stats(self):  
        
        FileName = 'RasterStatistics'
        filename, _filter = QFileDialog.getSaveFileName(  
            self.dlg, "Select output filename and destination",FileName, 'csv(*.csv)')  
        self.dlg.lnOutputStats.setText(filename)  

    def raster_processing(self):
        QgsMessageLog.logMessage('Processing button pressed ', 'vol test', Qgis.Info)
        elevation_change(self)


    def report_layout(self):
        QgsMessageLog.logMessage('Layout button pressed ', 'vol test', Qgis.Info)
        layout_report(self)
        
    def monography(self):
        QgsMessageLog.logMessage('Monography button pressed ', 'vol test', Qgis.Info)
        create_monograph(self)

    def close_dialog(self):
        self.dlg.close()

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = RasterTesterDialog()
            #Connect buttons for save files
            self.dlg.btnOutput.clicked.connect(self.select_output_file) 
            self.dlg.btnOutputStats.clicked.connect(self.select_output_file_stats)
            #Connect Accept and Cancel buttons in Processing Tab
            self.dlg.btnProcess.accepted.connect(self.raster_processing)
            self.dlg.btnProcess.rejected.connect(self.close_dialog)
            #Connect Accept and Cancel Buttons in Layout Tab
            self.dlg.btnLayout.accepted.connect(self.report_layout)
            self.dlg.btnLayout.rejected.connect(self.close_dialog) 
            #Connect Accept and Cancel Buttons in Monography Tab
            self.dlg.btnMono.accepted.connect(self.monography)
            self.dlg.btnMono.rejected.connect(self.close_dialog) 
            #Set respective filters for rasters and polygons
            self.dlg.cmbOld.setFilters(QgsMapLayerProxyModel.RasterLayer)
            self.dlg.cmbNew.setFilters(QgsMapLayerProxyModel.RasterLayer)
            self.dlg.cmbBB.setFilters(QgsMapLayerProxyModel.PolygonLayer)
            self.dlg.cmbLayoutPoints.setFilters(QgsMapLayerProxyModel.PointLayer)
            self.dlg.cmbMonoPoints.setFilters(QgsMapLayerProxyModel.PointLayer)
            #Connect Field Value Combo Box to cmbPoints
            self.dlg.cmbFieldValue.setLayer(self.dlg.cmbLayoutPoints.currentLayer())
            self.dlg.cmbFieldValue.setFilters(QgsFieldProxyModel.Numeric)
            #Connect Monography Feature to Monography Points
            self.dlg.cmbMonoFeat.setLayer(self.dlg.cmbMonoPoints.currentLayer())
            
             

        # show the dialog
        self.dlg.chkBB.clicked.connect(self.enable_bounding_box)
        self.dlg.chkStats.clicked.connect(self.enable_stats_box)
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            if self.dlg.btnProcess.accepted == True:
                self.raster_processing
            if self.dlg.btnLayout.accepted == True:
                self.report_layout
            if self.dlg.btnMono.accepted == True:
                self.create_monograph