import os
import csv
from qgis.PyQt.QtGui import QColor
from qgis.core import Qgis, QgsProject, QgsPrintLayout, QgsMessageLog, QgsLayoutItemMap, QgsLayoutPoint, \
     QgsUnitTypes, QgsApplication, QgsLayoutItemPage, QgsRasterBandStats, QgsColorRampShader,\
     QgsRasterShader, QgsSingleBandPseudoColorRenderer, QgsProcessing, QgsRasterLayer
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
from qgis.utils import iface
from PyQt5.QtWidgets import  QMessageBox
from qgis import processing

def create_layout(self, layout_name):
    """
    Layout Management: creates new layout and delete previous
    :param layout_name:
    :return
    :rtype:QgsLayout, QgsProject.instance().layoutManager()
    """
    project = QgsProject.instance()
    loManager = project.layoutManager()
    layouts = loManager.printLayouts()
    for layout in layouts:
        if layout.name() == layout_name:
            reply = QMessageBox.question(None, self.tr('Delete layout...'),
                                            self.tr(
                                                f"There's already a layout named {layout}\nDo you want to delete it?"),
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            try:
                if reply == QMessageBox.No:
                    return
                else:
                    loManager.removeLayout(layout)
                    QgsMessageLog.logMessage(f"Previous layout named {layout} removed... ", 'vol test', Qgis.Info)
            except:
                # in case ESC key is pressed to escape the dialog
                return

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(layout_name)
    return layout, loManager

def determine_orientation(self, extent, layout):
    """
    Determine and set the layout orientation
    :param extent: iface.mapCanvas().extent()
    :param layout: QgsLayout
    :rtype: bool, float, float, float, float, float
    """
    QgsMessageLog.logMessage("Creating a layout", 'vol test', Qgis.Info)
    map_width = extent.xMaximum() - extent.xMinimum()
    map_height = extent.yMaximum() - extent.yMinimum()
    page_size_name = QgsApplication.pageSizeRegistry().find(layout.pageCollection().page(0).pageSize())  # eg. 'A4' str
    
    #Define a checker to store if it is a landscape orientation
    landscape = False
    if map_width <= map_height:
            #It is a portrait
            
            QgsMessageLog.logMessage("Portrait layout", 'vol test', Qgis.Info)
            layout.pageCollection().page(0).setPageSize(page_size_name, QgsLayoutItemPage.Orientation.Portrait)
    else:
            #it is a landscape
            landscape = True
            QgsMessageLog.logMessage("Landscape layout", 'vol test', Qgis.Info)
            layout.pageCollection().page(0).setPageSize(page_size_name, QgsLayoutItemPage.Orientation.Landscape)
    
    #Define the scale ratio between layout size and map size
    layout_width = layout.pageCollection().page(0).pageSize().width()
    layout_height = layout.pageCollection().page(0).pageSize().height()

    if landscape:
            scale_ratio = (layout_width / map_width)
            if map_height * scale_ratio > layout_height:
                scale_ratio = map_height / layout_height
    else:
            scale_ratio =(layout_height / map_height)
            if map_width *scale_ratio > layout_width:
                scale_ratio = map_height / layout_height
    return landscape, layout_height, layout_width, map_height, map_width, scale_ratio

def determine_scale(self, landscape, layout, layout_height, layout_width, map_height, map_width, scale_ratio):
    """
    Define map scale
    :param landscape: boolean
    :param layout: QgsLayout
    :param layout_height: float
    :param layout_width: float
    :param map_height: float
    :param map_width: float
    :param scale_ratio: float
    :rtype: float, float, QgsLayoutItemMap
    """
    QgsMessageLog.logMessage("Defining Scale", 'vol test', Qgis.Info)
    my_map = QgsLayoutItemMap(layout)
    QgsMessageLog.logMessage(f"map width: {map_width}/n map height: {map_height}", 'vol test', Qgis.Info)
    QgsMessageLog.logMessage(f"scale ratio: {scale_ratio}", 'vol test', Qgis.Info)
    previous_height = map_height
    previous_width = map_width
    if landscape:
        map_width = layout_width
        map_height = round(map_height * scale_ratio, 3)  # makes qgis bug if not rounded 3
        # workaround don't know why in special case it has to be changed !:#
        if map_height > layout_height:
            map_height = layout_height
            map_width = round(previous_width / scale_ratio, 3)
    else:
        map_width = round(map_width * scale_ratio, 3)
        map_height = layout_height
        if map_width > map_height:
            map_width = layout_width
            map_height = round(previous_height / scale_ratio, 3)

    return map_height, map_width, my_map

def add_map(self, e, layout, layout_height, layout_width, map_height, map_width, margin, my_map):
    """
    Add map to the layout
    :param e: iface.mapCanvas().extent()
    :param layout: QgsLayout
    :param layout_height: float
    :param layout_width: float
    :param map_height: float
    :param map_width: float
    :param margin: float
    :param my_map: QgsLayoutItemMap
    :rtype: float, float, float, float
    """
    QgsMessageLog.logMessage("Adding map to layout", 'vol test', Qgis.Info)
    map_width = map_width - margin
    map_height = map_height - margin
    my_map.setRect(0, 0, map_width, map_height)
    my_map.setExtent(e)
    layout.addLayoutItem(my_map)
    my_map.refresh()
    map_real_width = my_map.rect().size().width()
    map_real_height = my_map.rect().size().height()
    x_offset = (layout_width - map_real_width) / 2
    y_offset = (layout_height - map_real_height) / 2
    my_map.setBackgroundColor(QColor(255, 255, 255, 255))
    my_map.setFrameEnabled(True)
    my_map.attemptMove(QgsLayoutPoint(x_offset, y_offset, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(my_map)
    return map_real_height, map_real_width, x_offset, y_offset

def run_layout(self, extent, layoutName):
        #The extent of the layput is the old Year Raster
        map_width = extent.xMaximum() - extent.xMinimum()
        map_height = extent.yMaximum() - extent.yMinimum()
        if (map_height==0) or (map_width==0):
            QgsMessageLog.logMessage("No loaded data - aborting", 'vol test', Qgis.Info)
            return


        try:
            layout, manager = create_layout(self, layoutName)
        except:
            # Quick and dirty. In case people decide not to replace previous layout
            QgsMessageLog.logMessage("Cancelled", 'vol test', Qgis.Info)
            return
        
        # Determine and set best layout orientation
        landscape, layout_height, layout_width,\
                map_height, map_width, \
                scale_ratio = determine_orientation(self, \
                                                    extent, layout)

        # Calculate scale
        map_height, map_width, my_map = determine_scale(self, landscape, \
                                                        layout, layout_height, layout_width,\
                                                            map_height, map_width, scale_ratio)

        # Add map
        add_map(self, extent, layout, layout_height, \
                layout_width, map_height, map_width, 10, my_map)

        manager.addLayout(layout)
        self.iface.openLayoutDesigner(layout)

def raster_symbology(rlayer):
     stats = rlayer.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
     min = stats.minimumValue
     max = stats.maximumValue
     fnc = QgsColorRampShader()
     fnc.setColorRampType(QgsColorRampShader.Interpolated)
     lst = [QgsColorRampShader.ColorRampItem(min, QColor('Red')),\
            QgsColorRampShader.ColorRampItem(max, QColor('Blue'))]
     fnc.setColorRampItemList(lst)
     shader = QgsRasterShader()
     shader.setRasterShaderFunction(fnc)
     renderer = QgsSingleBandPseudoColorRenderer(rlayer.dataProvider(), 1, shader)
     rlayer.setRenderer(renderer)

def clip_raster(rLayer, bBox):
     parameters = {'INPUT': rLayer,
            'MASK': bBox,
            'NODATA': -9999,
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': True,
            'OPTIONS': None,
            'DATA_TYPE': 0,
            'SOURCE_CRS': 'ProjectCrs',
            'TARGET_CRS': 'ProjectCrs',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
     clip = processing.run('gdal:cliprasterbymasklayer', parameters)
     clipRaster = QgsRasterLayer(clip['OUTPUT'])
     return clipRaster

def elevation_change(self):
    QgsMessageLog.logMessage('Processing task started ', 'vol test', Qgis.Info)
    #Declare name of output file from text in output box.
    outputFilename = self.dlg.lnOutput.text()
    #Get the first raster layer (older year)
    oldRasterName = self.dlg.cmbOld.currentText()
    #If there is more than one layer named the same it creates a list
    oldRaster = QgsProject.instance().mapLayersByName(oldRasterName)[0]
    # Verify at least one layer is opened
    if not oldRaster:
        QMessageBox.critical(self.dlg, "Missing layer", f"{oldRasterName} missing")
        QgsMessageLog.logMessage(f"Layer 1 {oldRasterName} missing, cancelling process ", 'vol test', Qgis.Info)
        return 
    QgsMessageLog.logMessage(f"Layer 1 {oldRasterName} loaded ", 'vol test', Qgis.Info)


    #Get the second raster layer (recent year)
    newRasterName = self.dlg.cmbNew.currentText()
    #If there is more than one layer named the same it creates a list
    newRaster = QgsProject.instance().mapLayersByName(newRasterName)[0]
    # Verify at least one layer is opened
    if not oldRaster:
        QMessageBox.critical(self.dlg, "Missing layer", f"{oldRasterName} missing")
        QgsMessageLog.logMessage(f"Layer 1 {oldRasterName} missing, cancelling process ", 'vol test', Qgis.Info)
        return 
    QgsMessageLog.logMessage(f"Layer 2 {newRasterName} loaded ", 'vol test', Qgis.Info)


    #Check CRS
    if newRaster.crs() != oldRaster.crs():
        reply = QMessageBox.question(None, self.tr('CRS does not match...'), \
                                        self.tr("The Layers are in different CRS, still want to continue?"),\
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
    #If layout is desired proceed to create layout
    if self.dlg.chkBB.isChecked():
        boundingBoxName = self.dlg.cmbBB.currentText()
        #If there is more than one layer named the same it creates a list so grab the first one
        boundingBox = QgsProject.instance().mapLayersByName(boundingBoxName)[0]
        newRaster = clip_raster(newRaster, boundingBox)
        QgsMessageLog.logMessage(f"CRS {newRaster.crs()}", 'vol test', Qgis.Info)
        oldRaster = clip_raster(oldRaster, boundingBox)


         
   
   
    #Get context and CRS
    context = QgsProject.instance().transformContext()
    oldCrs = oldRaster.crs()


    #sets up layer references
    oldRasterRef = QgsRasterCalculatorEntry()
    #In case there are 2 layers named the same, it grabs the first one
    oldRasterRef.raster=oldRaster
    oldRasterRef.bandNumber = 1
    oldRasterRef.crs = oldRaster.crs
    #The @1 is required for the formulaString
    oldRasterRef.ref = "oldRaster@1"
    
    
    #Repeat for new Raster
    newRasterRef=QgsRasterCalculatorEntry()
    #In case there are 2 layers named the same, it grabs the first one
    newRasterRef.raster=newRaster
    newRasterRef.bandNumber = 1
    newRasterRef.crs = newRaster.crs
    newRasterRef.ref = "newRaster@1"


    #Uses QgsRasterCalculator: https://api.qgis.org/api/classQgsRasterCalculator.html#abd4932102407a12b53036588893fa2cc
    #define entries for QgsRasterCalculator
    entries = []
    entries.append(newRasterRef)
    entries.append(oldRasterRef)
    #define Formula String. In this case New Raster - Old Raster to see changes from previous year to next
    formulaString = newRasterRef.ref + ' - ' + oldRasterRef.ref
    #Need to verify requirements with team. In this case, 
    # the operation is done with oldRaster's extent, cell width and height.
    differenceRaster = QgsRasterCalculator(formulaString,\
                                            outputFilename,\
                                            "GTiff",\
                                            oldRaster.extent(),\
                                            oldCrs,\
                                            oldRaster.width(), \
                                            oldRaster.height(),\
                                            entries,\
                                            context)
    QgsMessageLog.logMessage("Raster Calculation loaded", 'vol test', Qgis.Info)
    #Run calculation
    differenceRaster.processCalculation()
    QgsMessageLog.logMessage("Raster Calculation finished succesfully", 'vol test', Qgis.Info)
    rName = os.path.splitext(os.path.basename(outputFilename))[0]
    iface.addRasterLayer(outputFilename, rName)

    rasterDiff = QgsProject.instance().mapLayersByName(rName)
    stats = rasterDiff[0].dataProvider().bandStatistics(1, QgsRasterBandStats.All)
    totalDiff = stats.sum
    VolChange = totalDiff*0.2*0.2
    print(VolChange/1000000)


    #If layout is desired proceed to create layout
    if self.dlg.chkLayout.isChecked():
        layoutName = os.path.splitext(os.path.basename(outputFilename))[0]
        QgsMessageLog.logMessage("Layout is Checked", 'vol test', Qgis.Info)
        extent = oldRaster[0].extent()
        run_layout(self, extent, layoutName)
        #raster_symbology(rasterDiff[0])
        QgsMessageLog.logMessage("Layout Created", 'vol test', Qgis.Info)

    #If Save Stats is checked, proceed to create csv    
    if self.dlg.chkStats.isChecked():
        QgsMessageLog.logMessage("GetStatistics is Checked", 'vol test', Qgis.Info)
        outputFilenameStats = self.dlg.lnOutputStats.text()
        fieldnames = ['Statistic', 'Value']
        dict_data = [{'Statistic': 'Band_Number', 'Value': stats.bandNumber},\
                        {'Statistic': 'Mean', 'Value': stats.mean},\
                        {'Statistic': 'Std_Dev', 'Value': stats.stdDev},\
                        {'Statistic': 'Sum', 'Value': stats.sum},\
                        {'Statistic': 'Sum_of_Squares', 'Value': stats.sumOfSquares},\
                        {'Statistic': 'Minimum', 'Value': stats.minimumValue},\
                        {'Statistic': 'Maximum', 'Value': stats.maximumValue},\
                        {'Statistic': 'Range', 'Value': stats.range}]
        with open(outputFilenameStats, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames)
            writer.writeheader()
            for data in dict_data:
                writer.writerow(data)
        QgsMessageLog.logMessage("Statistics Exported", 'vol test', Qgis.Info)
    QgsMessageLog.logMessage("End of Processes", 'vol test', Qgis.Info)

                             
