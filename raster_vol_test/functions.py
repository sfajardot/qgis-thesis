import os
import csv
from qgis.PyQt.QtGui import QColor
from qgis.core import Qgis, QgsProject, QgsPrintLayout, QgsMessageLog, QgsLayoutItemMap, QgsLayoutPoint, \
     QgsUnitTypes, QgsApplication, QgsLayoutItemPage, QgsRasterBandStats,\
     QgsSingleSymbolRenderer, QgsVectorFieldSymbolLayer, QgsProcessing, QgsRasterLayer,\
     QgsGraduatedSymbolRenderer, QgsRendererRangeLabelFormat, QgsStyle ,\
     QgsClassificationEqualInterval, QgsClassificationJenks, QgsClassificationQuantile,\
     QgsRuleBasedRenderer, QgsLayoutSize, QgsLayoutItemPicture, QgsMarkerSymbol,\
     QgsLayoutItemLabel, QgsTextFormat, QgsVectorLayerSimpleLabeling, QgsPalLayerSettings,\
     QgsTextBufferSettings, QgsLayerTree, QgsLayoutItemLegend, QgsLayoutItemScaleBar,\
     QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsVectorLayer,\
     QgsRasterFileWriter, QgsRasterPipe
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry, QgsInterpolator,\
     QgsIDWInterpolator, QgsTinInterpolator, QgsGridFileWriter
from qgis.utils import iface
from PyQt5.QtWidgets import  QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QPointF
from qgis import processing



############ functions for Layout Tab #####################################################
def create_layout(self, layout_name):
    """
    Create a new print layout and remove any previous layout with the same name.

    This function checks if a layout with the specified `layout_name` already exists.
    If it exists, the user is prompted to delete it. Once confirmed or no prior layout exists, 
    a new layout is created.

    Args:
    - layout_name (str): The name of the layout to create or replace.

    Returns:
    - QgsPrintLayout: The newly created layout object.
    - QgsLayoutManager: The layout manager responsible for managing layouts within the project.
    """

    #This function is also used in the Monography tab
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
    Determine and set the layout orientation (portrait or landscape) based on the map extent dimensions.

    Args:
    - extent (QgsRectangle): The geographic extent of the map.
    - layout (QgsPrintLayout): The layout object where the orientation is applied.

    Returns:
    - bool: True if the layout is landscape, False if portrait.
    - float: The height of the layout.
    - float: The width of the layout.
    - float: The height of the map extent.
    - float: The width of the map extent.
    - float: The scale ratio between the layout and the map extent.
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
    Calculate and set the map scale for the layout.

    Args:
    - landscape (bool): Indicates if the layout is in landscape orientation.
    - layout (QgsPrintLayout): The layout object.
    - layout_height (float): The height of the layout page.
    - layout_width (float): The width of the layout page.
    - map_height (float): The height of the map extent.
    - map_width (float): The width of the map extent.
    - scale_ratio (float): The ratio between the layout size and map size.

    Returns:
    - float: Adjusted height of the map.
    - float: Adjusted width of the map.
    - QgsLayoutItemMap: The layout item map object added to the layout.
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
    Add the map to the layout with appropriate margins and centering.

    Args:
    - e (QgsRectangle): The extent of the map canvas.
    - layout (QgsPrintLayout): The layout object where the map is added.
    - layout_height (float): The height of the layout page.
    - layout_width (float): The width of the layout page.
    - map_height (float): The height of the map area.
    - map_width (float): The width of the map area.
    - margin (float): The margin to apply around the map.
    - my_map (QgsLayoutItemMap): The map item to be added to the layout.

    Returns:
    - float: The real height of the map after margins.
    - float: The real width of the map after margins.
    - float: The x-offset for centering the map.
    - float: The y-offset for centering the map.
    - QgsLayoutItemMap: The map item added to the layout.
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
    return map_real_height, map_real_width, x_offset, y_offset, my_map

def create_legend(layout, layer, map):
    """
    Create a legend for a map within the layout.

    Args:
    - layout (QgsPrintLayout): The layout to which the legend is added.
    - layer (QgsVectorLayer): The layer for which the legend is created.
    - map (QgsLayoutItemMap): The map item to link the legend.

    Returns:
    - QgsLayoutItemLegend: The legend item added to the layout.
    """
    root = QgsLayerTree()
    root.addLayer(layer)
    legend = QgsLayoutItemLegend(layout)
    legend.model().setRootGroup(root)
    legend.setLinkedMap(map)
    layout.addLayoutItem(legend)
    return legend

def create_north_arrow(layout):
    """
    Create a north arrow for the layout.

    This function adds a default north arrow (SVG format) to the specified layout. 
    The north arrow is loaded from the default QGIS resource.

    Args:
    - layout (QgsPrintLayout): The layout to which the north arrow is added.

    Returns:
    - QgsLayoutItemPicture: The north arrow item added to the layout.
    """
    north = QgsLayoutItemPicture(layout)
    north.setMode(QgsLayoutItemPicture.FormatSVG)
    north.setPicturePath(":/images/north_arrows/layout_default_north_arrow.svg")
    layout.addLayoutItem(north)
    return north

def create_scale_bar(layout, map):
    """
    Create a scale bar for the map in the layout.

    This function adds a scale bar to the layout and links it to the specified map.
    The scale bar is customized with the 'Single Box' style, uses kilometers as the unit, 
    and applies appropriate text formatting.

    Args:
    - layout (QgsPrintLayout): The layout to which the scale bar is added.
    - map (QgsLayoutItemMap): The map item to which the scale bar is linked.

    Returns:
    - QgsLayoutItemScaleBar: The scale bar item added to the layout.
    """
    scale = QgsLayoutItemScaleBar(layout)
    scale.setStyle('Single Box')
    scale_format = QgsTextFormat()
    scale_format.setFont(QFont("Times"))
    scale_format.setSize(12)
    scale.setTextFormat(scale_format)
    scale.applyDefaultSize(QgsUnitTypes.DistanceMeters)
    scale.setMapUnitsPerScaleBarUnit(1000)
    scale.setNumberOfSegments(2)
    scale.setUnitsPerSegment(1*500)
    scale.setUnitLabel("km")
    scale.setLinkedMap(map)
    scale.setBackgroundEnabled(True)
    layout.addLayoutItem(scale)
    return scale



def run_layout(self, extent, layoutName):
    """
    Run the full layout creation process, including orientation, scaling, and adding the map.

    Args:
    - extent (QgsRectangle): The extent of the old year raster.
    - layoutName (str): The name of the layout to create or replace.

    Returns:
    - my_map (QgsLayoutItemMap): The map item added to the layout..
    """
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
    _,_,_,_,my_map = add_map(self, extent, layout, layout_height, \
            layout_width, map_height, map_width, 10, my_map)

    manager.addLayout(layout)
    self.iface.openLayoutDesigner(layout)
    return my_map, layout

def graduated_symbology(self, layer, attribute_name, classification_method, num_classes):
    """
    Apply graduated symbology to a vector layer based on an attribute and classification method.

    :param layer: QgsVectorLayer object to which the symbology is applied.
    :param attribute_name: Name of the attribute to classify.
    :param sym_type: The type of symbology ('Graduated').
    :param classification_method: The classification method ('Equal Interval', 'Jenks', 'Quantile').
    :param num_classes: Number of classes for graduated rendering.
    :return: None.
    """
    ramp_name = 'Spectral'   
    method = {'Equal Interval': QgsClassificationEqualInterval(),\
                'Jenks': QgsClassificationJenks(),\
                'Quantile': QgsClassificationQuantile()}.get(classification_method)
    field_index = layer.fields().lookupField(attribute_name)
    if not field_index:
            QMessageBox.critical(self.dlg, "Attribute not found", f"Attribute {attribute_name} not found")
            return
    values = layer.dataProvider().uniqueValues(field_index)
    if len(values)<2:
            QMessageBox.critical(self.dlg, "Not Enough Values", f"{attribute_name} does not have enough unique values")
            return

    #Change format setting as necessary
    format = QgsRendererRangeLabelFormat()
    format.setFormat("%1 - %2")
    format.setPrecision(2)
    format.setTrimTrailingZeroes(True)
    
    #Apply the renderer
    default_style = QgsStyle().defaultStyle()
    color_ramp = default_style.colorRamp(ramp_name)

    renderer = QgsGraduatedSymbolRenderer()
    renderer.setClassAttribute(attribute_name)
    renderer.setClassificationMethod(method)
    renderer.setLabelFormat(format)
    renderer.updateClasses(layer, num_classes)
    renderer.updateColorRamp(color_ramp)

    layer.setRenderer(renderer)
    layer.triggerRepaint()

def vector_field_symbology(self, layer, xMag, yMag, scaleFactor):
    """
    Apply vector field symbology to a vector layer.

    This function sets up a vector field symbology on a given vector layer, using two attributes 
    (xMag and yMag) representing the eastward and northward displacements. The scale factor is 
    applied to adjust the size of the arrows representing the vector field.

    Args:
    - layer (QgsVectorLayer): The vector layer to which the symbology is applied.
    - xMag (str): The field name for the eastward displacement (X component of the vector).
    - yMag (str): The field name for the northward displacement (Y component of the vector).
    - scaleFactor (float): The scale factor applied to the vector field symbols.

    Returns:
    - None: The function directly modifies the layer's symbology and repaints it.
    """
    
    # Create a symbol with a vector field symbol layer
    symbol = QgsMarkerSymbol.createSimple({'name': 'circle', 'size': '3'})
    
    # Define the attributes for vector field
    east_field = xMag 
    north_field = yMag

    # Create the vector field symbol layer
    vector_field = QgsVectorFieldSymbolLayer.create()
    vector_field.setXAttribute(east_field)
    vector_field.setYAttribute(north_field)
    vector_field.setScale(scaleFactor)
    vector_field.setColor(QColor("black"))



    if vector_field:
        # Add vector field symbol layer to the symbol
        symbol.changeSymbolLayer(0, vector_field)

        # Set the symbol for the layer
        renderer = QgsSingleSymbolRenderer(symbol)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
    else:
        QMessageBox.critical(self.dlg, "Vector Field Error", "Failed to create vector field symbol layer")



def symbolized_map(self, cmbLayoutPoints, cmbFieldValue, cmbGradMeth, spbNumClass, cmbSymType, lnLayoutName, cmbXMag, cmbYMag, spbScale ):
    """
    Apply symbology and create a map layout with specified parameters.

    :param cmbLayoutPoints: ComboBox for the vector layer to be used.
    :param cmbFieldValue: ComboBox to select the attribute field for symbology.
    :param cmbGradMeth: ComboBox to select classification method ('Equal Interval', 'Jenks', etc.).
    :param spbNumClass: SpinBox for the number of classification classes.
    :param cmbSymType: ComboBox to select the type of symbology ('Graduated').
    :param lnLayoutName: LineEdit for specifying the layout name.
    :return: None.
    """
    layer = cmbLayoutPoints.currentLayer()
    attribute_name = cmbFieldValue.currentField()
    classification_method = cmbGradMeth.currentText()
    num_class = spbNumClass.value()
    sym_type = cmbSymType.currentText()
    xMag = cmbXMag.currentField()
    yMag = cmbYMag.currentField()
    scaleFactor = spbScale.value()

    if sym_type == 'Graduated':
        graduated_symbology(self, layer, attribute_name, classification_method, num_class)
    elif sym_type == 'Vector Field Marker':
        vector_field_symbology(self, layer, xMag, yMag, scaleFactor)

    
    layoutName = lnLayoutName.text()
    if not layoutName:
        layoutName = "Report Layout"
    QgsMessageLog.logMessage(f"Layout {layoutName} being created", 'vol test', Qgis.Info)
    points = cmbLayoutPoints.currentLayer()
    #Adds a 10% buffer to the extent of the map so corner points are more visible
    extent = points.extent().buffered(points.extent().width()*0.1)
    my_map, layout= run_layout(self, extent, layoutName)
    map_pos = my_map.pagePos()
    QgsMessageLog.logMessage("Layout Created", 'vol test', Qgis.Info)
    map_width = my_map.boundingRect().width()
    map_height = my_map.boundingRect().height()
    #Adds legend to map
    ## CURRENTLY UNAVAILABLE DUE TO QGIS CRASH< NO DOCUMENTATION ON HOW TO FIX QGIS bug
    #legend = create_legend(layout, layer, my_map)
    north = create_north_arrow(layout)
    north.attemptResize(QgsLayoutSize(10,10))
    north.attemptMove(QgsLayoutPoint(map_pos), QgsUnitTypes.LayoutMillimeters)

    scale = create_scale_bar(layout, my_map)
    scale.attemptResize(QgsLayoutSize(map_width, 13.2))
    scale_pos = map_pos + QPointF(0, map_height - scale.boundingRect().height())
    scale.attemptMove(QgsLayoutPoint(scale_pos), QgsUnitTypes.LayoutMillimeters)
########################################################################################

######################### Functions for Processing Tab #################################
def clip_raster(rLayer, bBox):
    """
    Clip a raster layer by a bounding box (mask layer).

    :param rLayer: The input raster layer to be clipped.
    :param bBox: The bounding box (mask) vector layer to clip the raster.
    :return: The clipped QgsRasterLayer object.
    """
    bBox_crs = bBox.crs()
    rLayer_crs = rLayer.crs()
    if  bBox_crs != rLayer_crs:
        QgsMessageLog.logMessage("Reprojecting bounding box", 'vol test', Qgis.Info)
        parameters = {'INPUT': bBox,
                     'TARGET_CRS': rLayer_crs.authid(),
                     'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
        reproj = processing.run('native:reprojectlayer', parameters)['OUTPUT']
    else:
        reproj = bBox


    parameters = {'INPUT': rLayer,
           'MASK': reproj,
           'NODATA': -9999,
           'ALPHA_BAND': False,
           'CROP_TO_CUTLINE': True,
           'KEEP_RESOLUTION': True,
           'OPTIONS': None,
           'DATA_TYPE': 0,
           'SOURCE_CRS': rLayer_crs.authid(),
           'TARGET_CRS': rLayer_crs.authid(),
           'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT}
    clip = processing.run('gdal:cliprasterbymasklayer', parameters)
    clipRaster = QgsRasterLayer(clip['OUTPUT'])
    return clipRaster

def get_stats(self, rLayer, lnOutputStats):
    """
    Generate statistics for a raster layer and save them to a CSV file.

    :param rLayer: The input raster layer to analyze.
    :param lnOutputStats: LineEdit providing the output file path for the CSV file.
    :return: None.
    """
    stats = rLayer.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
    outputFilenameStats = lnOutputStats.text()
    if not outputFilenameStats:
         QMessageBox.critical(self.dlg, "No Output Path", "Missing Output Save Name for Statistics File")
         return
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
    
def create_raster_entry(raster, ref_name):
    """
    Helper function to create a raster entry for raster calculations.

    :param raster: The input raster layer.
    :param ref_name: Reference name to be used in the raster calculator.
    :return: QgsRasterCalculatorEntry object.
    """
    raster_entry = QgsRasterCalculatorEntry()
    raster_entry.raster = raster
    raster_entry.bandNumber = 1
    raster_entry.ref = f"{ref_name}@1"
    return raster_entry

def get_raster_layer(self, combo_box, layer_type):
    """
    Helper function to load a raster layer from a combo box.

    :param combo_box: ComboBox widget containing the list of available raster layers.
    :param layer_type: String description of the raster layer type ('Old Raster', 'New Raster').
    :return: The loaded QgsRasterLayer if available, else None.
    """
    raster_name = combo_box.currentText()
    raster_layer = combo_box.currentLayer()
    if not raster_layer:
        QMessageBox.critical(self.dlg, f"Missing {layer_type} layer", f"{raster_name} missing")
        QgsMessageLog.logMessage(f"{layer_type} layer '{raster_name}' missing, cancelling process", 'vol test', Qgis.Info)
        return None
    QgsMessageLog.logMessage(f"{layer_type} layer '{raster_name}' loaded", 'vol test', Qgis.Info)
    return raster_layer

def elevation_change(self, lnOutput, cmbOld, cmbNew, chkBB, cmbBB, chkStats, lnOutputStats, chkChangeType):
    """
    Perform elevation change calculation between two raster layers.

    This function calculates the difference between two raster layers, representing the change in elevation
    (or other data values) over time or between two datasets. It performs the following key steps:

    1. Retrieves the output file path from the user interface.
    2. Loads two raster layers (referred to as 'Old Raster' and 'New Raster') via the provided combo boxes.
    3. Checks if the Coordinate Reference Systems (CRS) of the two rasters match, and prompts the user to confirm if they don't.
    4. Optionally clips the raster layers to a bounding box if this option is selected in the UI.
    5. Performs raster calculations by subtracting the 'Old Raster' values from the 'New Raster' values.
    6. Saves the output raster as a GeoTIFF file to the specified path.
    7. Optionally calculates and saves statistics for the difference raster if that option is selected.
    8. Adds the resulting difference raster to the QGIS project.

    Required Inputs:
    :param lnOutput: LineEdit widget providing the output raster file path.
    :param cmbOld: ComboBox widget containing the old raster layer.
    :param cmbNew: ComboBox widget containing the new raster layer.
    :param chkBB: CheckBox widget indicating if the rasters should be clipped to a bounding box.
    :param cmbBB: ComboBox widget providing the bounding box (mask layer) if clipping is enabled.
    :param chkStats: CheckBox widget indicating if statistics should be calculated and saved for the output raster.
    :param lnOutputStats: LineEdit widget providing the file path to save statistics in CSV format.

    Returns:
    - The function performs calculations and raster operations, and either displays the result as a new raster layer in the QGIS project or shows an error if the process fails.
    """
    QgsMessageLog.logMessage('Processing task started', 'vol test', Qgis.Info)

    # Get output file path
    output_filename = lnOutput.text()
    if not output_filename:
        QMessageBox.critical(self.dlg, "No Output Path", "Missing Output Save Name")
        return

    # Load old and new raster layers
    old_raster = get_raster_layer(self, cmbOld, "Old Raster")
    if not old_raster:
        return
    new_raster = get_raster_layer(self, cmbNew, "New Raster")
    if not new_raster:
        return

    # Check if CRS matches between old and new rasters
    if new_raster.crs() != old_raster.crs():
        reply = QMessageBox.question(
            None, self.tr('CRS Mismatch'),
            self.tr("The Layers are in different CRS. Do you want to continue?"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

    # Clip rasters if bounding box is checked
    if chkBB.isChecked():
        bounding_box = cmbBB.currentLayer()
        if bounding_box:
            new_raster = clip_raster(new_raster, bounding_box)
            old_raster = clip_raster(old_raster, bounding_box)
            QgsMessageLog.logMessage(f"Rasters clipped using bounding box. CRS: {new_raster.crs()}", 'vol test', Qgis.Info)

    # Set up raster calculator entries
    old_raster_ref = create_raster_entry(old_raster, "oldRaster")
    new_raster_ref = create_raster_entry(new_raster, "newRaster")


    # Get area of reference pixel
    pixel_area = old_raster.rasterUnitsPerPixelX()*old_raster.rasterUnitsPerPixelY()
    # Perform raster calculation (New Raster - Old Raster)
    # Check if it should be calculated as volume
    if chkChangeType.isChecked():
        formula_string = f"({new_raster_ref.ref} - {old_raster_ref.ref})*{pixel_area}"
    else:
        formula_string = f"{new_raster_ref.ref} - {old_raster_ref.ref}"
    entries = [new_raster_ref, old_raster_ref]

    difference_raster = QgsRasterCalculator(
        formula_string,
        output_filename,
        "GTiff",
        old_raster.extent(),
        old_raster.crs(),
        old_raster.width(),
        old_raster.height(),
        entries,
        QgsProject.instance().transformContext()
    )

    QgsMessageLog.logMessage("Raster calculation started", 'vol test', Qgis.Info)
    if difference_raster.processCalculation() == 0:
        QgsMessageLog.logMessage("Raster calculation finished successfully", 'vol test', Qgis.Info)
        r_name = os.path.splitext(os.path.basename(output_filename))[0]
        iface.addRasterLayer(output_filename, r_name)

        # If 'Save Stats' is checked, generate statistics
        if chkStats.isChecked():
            QgsMessageLog.logMessage("Saving statistics is checked", 'vol test', Qgis.Info)
            raster_diff = QgsProject.instance().mapLayersByName(r_name)
            if raster_diff:
                get_stats(self, raster_diff[0], lnOutputStats)
    else:
        QMessageBox.critical(self.dlg, "Error", "Raster calculation failed.")
        QgsMessageLog.logMessage("Raster calculation failed", 'vol test', Qgis.Critical)
################################################################################################

################### Functions for Monography Tab################################################

def create_text(layout, text, font_size, font = 'Times', bold = False, frame = True, HAlign = True, VAlign = True):
    """
    Helper function to create a textbox in the layout.

    Args:
        layout (QgsLayout): The layout to which the textbox will be added.
        text (str): The content of the textbox.
        font_size (int): Size of the text.
        font (str): Font type, default is 'Times'.
        bold (bool): Whether the text is bold, default is False.
        frame (bool): Whether a frame around the textbox is enabled, default is True.
        HAlign (bool): Whether the text is horizontally aligned (centered), default is True.
        VAlign (bool): Whether the text is vertically aligned (centered), default is True.

    Returns:
        QgsLayoutItemLabel: The created textbox item.
    """
    txtbox = QgsLayoutItemLabel(layout)
    txtbox.setText(str(text))
    txtbox_format = QgsTextFormat()
    txtbox_format.setFont(QFont(font))
    txtbox_format.setSize(font_size)
    txtbox_format.setForcedBold(bold)
    txtbox.setTextFormat(txtbox_format)
    txtbox.setFrameEnabled(frame)
    if HAlign:
         txtbox.setHAlign(Qt.AlignCenter)
    if VAlign:
         txtbox.setVAlign(Qt.AlignCenter)
    layout.addLayoutItem(txtbox)
    return txtbox

def create_image(layout, filepath, idName):
    """
    Helper function to create an image from a .jpg or .png file in the layout.

    Args:
        layout (QgsLayout): The layout to which the image will be added.
        filepath (str): Path to the image file.
        idName (str): Identifier for the image.

    Returns:
        QgsLayoutItemPicture: The created image item.
    """
    picture = QgsLayoutItemPicture(layout)
    picture.setPicturePath(filepath)
    picture.setId(idName)
    picture.setPictureAnchor(4)
    layout.addLayoutItem(picture)
    return picture

def map_single_point_with_labels(layout, feature, layer):
    """
    Function that changes the symbology of a point layer to display only the selected feature
    and adds a label to it.

    Args:
        layout (QgsLayout): The layout to which the map will be added.
        feature (QgsFeature): The selected feature to be displayed and labeled.
        layer (QgsVectorLayer): The vector layer containing the feature.

    Returns:
        QgsLayoutItemMap: The map item with the selected feature and label.
    """
    #Add Map
    map = QgsLayoutItemMap(layout)

    #Necessary to create map, gets overriden later with the extent
    map.setRect(20,20,20,20)

    #Set up red color symbology for selected feature
    symbol = QgsMarkerSymbol.createSimple({'color': 'red', 'size': '5'})

    # Create a rule-based renderer to apply the symbology only to the selected feature
    expression = f'"id" = {feature.id()}'  # Use field name directly
    
    # Create the root rule (with no filter)
    root_rule = QgsRuleBasedRenderer.Rule(None)
    
    # Create a rule for the selected feature with the red symbol
    rule = QgsRuleBasedRenderer.Rule(symbol)
    rule.setFilterExpression(expression)  # Set the expression as a string
    
    # Add the rule to the root rule
    root_rule.appendChild(rule)

    # Set the rule-based renderer to the points layer
    renderer = QgsRuleBasedRenderer(root_rule)
    layer.setRenderer(renderer)

    # Refresh the layer to apply the new renderer
    layer.triggerRepaint()

    # Set up labeling
    settings = QgsPalLayerSettings()
    
    # Enable labeling and set the field for the label
    settings.fieldName = "label"  # Assuming the field name is 'label'
    settings.enabled = True

    # Customize the font
    text_format = QgsTextFormat()
    text_format.setFont(QFont("Times"))  # Set font family and size
    text_format.setSize(18)  # Set label size

    # Set up text buffer (mask)
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(1.5)  # Adjust the buffer size
    buffer.setColor(QColor("white"))  # Set buffer color (white)
    text_format.setBuffer(buffer)

    # Apply the text format (font + buffer) to the settings
    settings.setFormat(text_format)
    
    # Apply label settings to the layer
    labeling = QgsVectorLayerSimpleLabeling(settings)
    layer.setLabelsEnabled(True)
    layer.setLabeling(labeling) 

    # Refresh the map canvas to show labels
    layer.triggerRepaint()
    return map

def sort_dates(dates):
    # Sorting QDate objects from most recent to oldest
    sorted_dates = sorted(dates, key=lambda dt: dt.toJulianDay(), reverse=True)

    # Convert sorted QDate objects to 'dd-MM-yy' string format
    sorted_date_strings = [date.toString("dd-MM-yy") for date in sorted_dates]
    return sorted_date_strings, sorted_dates



def get_matching_features(selected_feature, field_name, layer):
    selected_value = selected_feature[field_name]
    matching_features = []
    for feature in layer.getFeatures():
        if feature[field_name] == selected_value:
            matching_features.append(feature)
    return matching_features

def get_sorted_by_date_features(sorted_qdates, features, date_attribute):
    sorted_features = []
    for date in sorted_qdates:
        for feature in features:
            if feature[date_attribute] == date:
                sorted_features.append(feature)
    return sorted_features



def create_monograph(self, cmbMonoPoints, cmbMonoFeat, txtTrgClr, txtTrgDscr, txtGnss,
                      lnLogo, lnPhoto_1, lnPhoto_2, lnInst, cmbFieldLabel, cmbFieldSurvey,
                       spbNumSrvy, cmbHeight):
    """
    Function to create a monograph layout according to the Polimi Belvedere Glacier Monitoring Project format.

    Args:
        self: The reference to the calling object.
        cmbMonoPoints (QComboBox): The combobox to select the layer with monograph points.
        cmbMonoFeat (QgsFeatureSelectionModel): The selected feature to create the monograph.
        txtTrgClr (QTextEdit): The textbox with the target color description.
        txtTrgDscr (QTextEdit): The textbox with the target description.
        txtGnss (QTextEdit): The textbox with the GNSS mode.
        lnLogo (QLineEdit): The line edit with the file path for the Institution logo.
        lnPhoto_1 (QLineEdit): The line edit with the file path for the first photo.
        lnPhoto_2 (QLineEdit): The line edit with the file path for the second photo.


    Returns:
        None
    """
    layer = cmbMonoPoints.currentLayer()
    if not layer:
       QMessageBox.critical(self.dlg, "No Layer loaded", "Missing Point Layer")
       return
    
    #Get the field names for surveys and labels
    label_field = cmbFieldLabel.currentField()
    survey_field = cmbFieldSurvey.currentField()
    h_field = cmbHeight.currentField()
    label_name = cmbMonoFeat.currentText()

    #Filter layer to use only the features with the label name chosen
    expression = f'\"{label_field}\" = \'{label_name}\''
    layer.setSubsetString(expression)

    

    #Get number of surveys
    num_srvy = spbNumSrvy.value()

    

    #Add here other values to be taken from
    srvy_list = []
    unsorted_features =[]
    for ft in layer.getFeatures():
        srvy_list.append(ft[survey_field])
        unsorted_features.append(ft)
    #Since we have saved the filtered features we can get rid of the query
    layer.setSubsetString('')

    srvy_sorted_list, sorted_qdates = sort_dates(srvy_list)

    features = get_sorted_by_date_features(sorted_qdates, unsorted_features, survey_field)
    print(features)


    h_ell =[]
    est = []
    nord = []
    lon = []
    lat = []



    for ft in features:
        geom = ft.geometry()
        geom2 = QgsGeometry(geom)
        sourceCrs = layer.crs()
        destCrs = QgsCoordinateReferenceSystem("EPSG:4326")
        tr = QgsCoordinateTransform()
        tr.setSourceCrs(sourceCrs)
        tr.setDestinationCrs(destCrs)
        geom2.transform(tr)
        h_ell.append(ft[h_field])
        lon_float = geom2.asPoint().x()
        lat_float = geom2.asPoint().y()
        lon.append(f"{lon_float:.9f}")
        lat.append(f"{lat_float:.9f}")
        est.append(geom.asPoint().x())
        nord.append(geom.asPoint().y())

    
    val_mat = [lat, lon, h_ell, est, nord]

    #Get the most recent feature from the list to use as base
    feature = features[0]


    #Get descriptions
    target_color = txtTrgClr.toPlainText()
    target_description = txtTrgDscr.toPlainText()
    gnss_type = txtGnss.toPlainText()
    
    layout_name = str(label_name)+'_'+srvy_sorted_list[0]

    #Determine type of Ground Control Point
    gcp_bool = feature["is_fixed"]
    if gcp_bool == 'false':
         gcp_type = 'MOBILE'
    else:
         gcp_type = 'FIXED'

    #Create layout and open it
    layout, manager = create_layout(self, layout_name)
    pc = layout.pageCollection()
    pc.page(0).setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)
    manager.addLayout(layout)
    y_pos = 7.5

    #Set title label
    title = create_text(layout, text = label_name, font_size = 36)
    title.setFixedSize(QgsLayoutSize(97.5, 20))
    title.attemptMove(QgsLayoutPoint(7.5, y_pos, QgsUnitTypes.LayoutMillimeters))

    #Set Institution headers
    inst_text = lnInst.text()
    inst = create_text(layout, inst_text, font_size = 10, HAlign = False)
    inst.setFixedSize(QgsLayoutSize(75, 20))
    inst.attemptMove(QgsLayoutPoint(127.5, y_pos, QgsUnitTypes.LayoutMillimeters))
    inst_path = lnLogo.text()
    inst_logo = create_image(layout, inst_path, 'InstLogo')
    inst_logo.attemptMove(QgsLayoutPoint(105, y_pos, QgsUnitTypes.LayoutMillimeters))
    inst_logo.setFixedSize(QgsLayoutSize(22.5,20))
    inst_logo.setFrameEnabled(True)

    y_pos += inst.boundingRect().height()

    #Add Descriptions
    crs_txt = sourceCrs.description()
    dscr_text = f"Target Color: {target_color}\n\nDescription: {target_description}\nGCP Type: {gcp_type}\n\nType of GNSS: {gnss_type}\nCRS: {crs_txt}"
    dscr = create_text(layout, dscr_text, font_size = 12, VAlign = False, HAlign = False)
    dscr.setFixedSize(QgsLayoutSize(195, 50))
    dscr.setMarginX(0.5)
    dscr.setMarginY(0.25)
    dscr.attemptMove(QgsLayoutPoint(7.5, y_pos, QgsUnitTypes.LayoutMillimeters))
    y_pos += dscr.boundingRect().height()
    
    #Get the number of rows and columns in the QTableWidget
    if num_srvy>len(srvy_sorted_list):
        rows = range(0, len(srvy_sorted_list))
    else:
        rows = range(0, num_srvy)

    cols = ['Lat (j)', 'Long (I)', 'H_ell [m]', 'Est [m]', 'Nord [m]']

    # Here textboxes are created instead of a layout table in the layout because the layout table 
    # is not editable and is saved as a static image, thus making editing and proofreading hard
    
    #Iterate over rows in the QTable
    for row in rows:
         srvy_date = srvy_sorted_list[row]
         if srvy_date != None:
            # This first parts creates the title of the table as the survey date given
            srvy_text = 'Coordinates: ' + srvy_date
            srvy = create_text(layout, srvy_text, font_size = 12, bold = True)
            srvy.setFixedSize(QgsLayoutSize(195, 7.5))
            srvy.attemptMove(QgsLayoutPoint(7.5, y_pos, QgsUnitTypes.LayoutMillimeters))
            y_pos += srvy.boundingRect().height()
            # Establishes the X margin counter
            x_marg = 7.5
            #Iterates over the columns to create the textboxes from left to right of the headers
            for col in cols:
                head_txt = col
                head = create_text(layout, head_txt, font_size = 12)
                head.setFixedSize(QgsLayoutSize(195/len(cols)-(0.25), 10))
                head.attemptMove(QgsLayoutPoint(x_marg, y_pos, QgsUnitTypes.LayoutMillimeters))
                x_marg += head.boundingRect().width()
            #Resets the x_marg to initial value
            x_marg = 7.5
            # Adds the height of the headers to y_pos
            y_pos += head.boundingRect().height()
            # Iterates to add the values to each header. This is done in a second for loop to not have to add and substract
            # the y_pos every time. It can be probably optimized.
            for col in range(0, len(cols)):
                val_txt = str(val_mat[col][row])
                value = create_text(layout, val_txt, font_size = 12)
                value.setFixedSize(QgsLayoutSize((195/len(cols))-(0.25), 10))
                value.attemptMove(QgsLayoutPoint(x_marg, y_pos, QgsUnitTypes.LayoutMillimeters))
                x_marg += value.boundingRect().width()
            y_pos += value.boundingRect().height()

    #Create Photo Title
    photo_txt = "ORTOFOTO"
    photo_title = create_text(layout, photo_txt, 12, bold = True)
    photo_title.setFixedSize(QgsLayoutSize(195,7.5))
    photo_title.attemptMove(QgsLayoutPoint(7.5, y_pos))
    y_pos += photo_title.boundingRect().height()

    #Creates the map with the desired symbology for the monography.
    map = map_single_point_with_labels(layout, feature, layer)
    #Moves map and sets size
    map.setFixedSize(QgsLayoutSize(97.5, 297-7.5-y_pos))
    map.attemptMove(QgsLayoutPoint(7.5, y_pos, QgsUnitTypes.LayoutMillimeters))
    map.setFrameEnabled(True)
    #Gets extent from the layer of GCPs and sets it to the map
    extent = layer.extent().buffered(layer.extent().width()*0.2)
    map.setExtent(extent)
    map.zoomToExtent(extent)
    layout.addLayoutItem(map)
    # Add scale bar
    scale = create_scale_bar(layout, map)
    scale.attemptResize(QgsLayoutSize(10,10))
    scale_pos = y_pos + map.boundingRect().height()- scale.boundingRect().height() -1
    scale.attemptMove(QgsLayoutPoint(8.5, scale_pos))
    #Add North Arrow
    north = create_north_arrow(layout)
    north.attemptResize(QgsLayoutSize(10,10))
    north_pos = map.pagePos()
    north.attemptMove(QgsLayoutPoint(north_pos, QgsUnitTypes.LayoutMillimeters))


    ##Add Description Images
    #Upper right image
    photo_up_path = lnPhoto_1.text()
    if photo_up_path:
        photo_upper = create_image(layout, photo_up_path, 'PhotoUpper')
        photo_upper.attemptMove(QgsLayoutPoint(105, y_pos, QgsUnitTypes.LayoutMillimeters))
        photo_upper.setFixedSize(QgsLayoutSize(97.5,((297-7.5-y_pos)/2)))
        photo_upper.setFrameEnabled(True)
        y_pos += photo_upper.boundingRect().height()
    #Lower right image
    photo_low_path = lnPhoto_2.text()
    photo_lower = create_image(layout, photo_low_path, 'PhotoLower')
    photo_lower.attemptMove(QgsLayoutPoint(105, y_pos, QgsUnitTypes.LayoutMillimeters))
    photo_lower.setFixedSize(QgsLayoutSize(97.5,((297-7.5-y_pos))))
    photo_lower.setFrameEnabled(True)

    #Open layout
    self.iface.openLayoutDesigner(layout)
##########################################################################################

#######Interpolator functions###################


def interpolator(self, cmbInterpolationLayer, cmbInterpolationField, cmbInterpolationType, lnOutputInter, 
                 spbResolution, spbWeight, lnInterFilter):
    output_path = lnOutputInter.text()
    layer = cmbInterpolationLayer.currentLayer()
    if not layer:
       QMessageBox.critical(self.dlg, "No Layer loaded", "Missing Point Layer")
       return
    field = cmbInterpolationField.currentField()
    if not field:
       QMessageBox.critical(self.dlg, "No Field Found", "Missing Field")
       return
    
    if lnInterFilter.currentText() != '':
        QgsMessageLog.logMessage("Filtering needed", 'vol test', Qgis.Info)
        layer.setSubsetString(lnInterFilter.asExpression())
    else:
        QgsMessageLog.logMessage("No filtering needed", 'vol test', Qgis.Info)
    fields = layer.fields()
    idxField = fields.indexFromName(field)
    inter_type = cmbInterpolationType.currentText()
    res = spbResolution.value()
    weight = spbWeight.value()
    rect = layer.extent()
    ncol = int((rect.xMaximum() - rect.xMinimum())/res)
    nrow = int((rect.yMaximum() - rect.yMinimum())/res)
    layer_data = QgsInterpolator.LayerData()
    layer_data.source = layer
    layer_data.zCoordInterpolation=False
    layer_data.interpolationAttribute = idxField
    layer_data.sourceType = 0 
    r_name = os.path.splitext(os.path.basename(output_path))[0]
    if inter_type == 'IDW':
        idw_interpolator = QgsIDWInterpolator([layer_data])
        idw_interpolator.setDistanceCoefficient(weight)
        output = QgsGridFileWriter(idw_interpolator, output_path, rect, ncol, nrow)
        output.writeFile()
        #TIN Interpolation is not giving expected values
    if inter_type == 'TIN':
        tin_interpolation_method = QgsTinInterpolator.Linear
        tin_interpolator = QgsTinInterpolator([layer_data], tin_interpolation_method)
        output = QgsGridFileWriter(tin_interpolator, output_path, rect, ncol, nrow)
        output.writeFile()

    iface.addRasterLayer(output_path, r_name)


    if lnInterFilter.currentText() != '':
        layer.setSubsetString('')




    