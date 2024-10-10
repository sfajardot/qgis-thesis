import os
import csv
from qgis.PyQt.QtGui import QColor
from qgis.core import Qgis, QgsProject, QgsPrintLayout, QgsMessageLog, QgsLayoutItemMap, QgsLayoutPoint, \
     QgsUnitTypes, QgsApplication, QgsLayoutItemPage, QgsRasterBandStats, QgsColorRampShader,\
     QgsRasterShader, QgsSingleBandPseudoColorRenderer, QgsProcessing, QgsRasterLayer,\
     QgsGraduatedSymbolRenderer, QgsRendererRangeLabelFormat, QgsStyle ,\
     QgsClassificationEqualInterval, QgsClassificationJenks, QgsClassificationQuantile,\
     QgsRuleBasedRenderer, QgsLayoutSize, QgsLayoutItemPicture, QgsMarkerSymbol,\
     QgsLayoutItemLabel, QgsTextFormat, QgsVectorLayerSimpleLabeling, QgsPalLayerSettings,\
     QgsTextBufferSettings
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
from qgis.utils import iface
from PyQt5.QtWidgets import  QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
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
def graduated_symbology(self, layer, attribute_name, sym_type, classification_method, num_classes):
    if sym_type == 'Graduated': 
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
    #if sym_type == 'Vector Field Marker':
    #    renderer = 

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

def get_stats(self, rLayer):
    stats = rLayer.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
    outputFilenameStats = self.dlg.lnOutputStats.text()
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

def elevation_change(self):
    """Perform elevation change calculation between two raster layers."""
    QgsMessageLog.logMessage('Processing task started', 'vol test', Qgis.Info)

    # Get output file path
    output_filename = self.dlg.lnOutput.text()
    if not output_filename:
        QMessageBox.critical(self.dlg, "No Output Path", "Missing Output Save Name")
        return

    # Helper function to load raster layers
    def get_raster_layer(combo_box, layer_type):
        raster_name = combo_box.currentText()
        raster_layer = combo_box.currentLayer()
        if not raster_layer:
            QMessageBox.critical(self.dlg, f"Missing {layer_type} layer", f"{raster_name} missing")
            QgsMessageLog.logMessage(f"{layer_type} layer '{raster_name}' missing, cancelling process", 'vol test', Qgis.Info)
            return None
        QgsMessageLog.logMessage(f"{layer_type} layer '{raster_name}' loaded", 'vol test', Qgis.Info)
        return raster_layer

    # Load old and new raster layers
    old_raster = get_raster_layer(self.dlg.cmbOld, "Old Raster")
    if not old_raster:
        return
    new_raster = get_raster_layer(self.dlg.cmbNew, "New Raster")
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
    if self.dlg.chkBB.isChecked():
        bounding_box = self.dlg.cmbBB.currentLayer()
        if bounding_box:
            new_raster = clip_raster(new_raster, bounding_box)
            old_raster = clip_raster(old_raster, bounding_box)
            QgsMessageLog.logMessage(f"Rasters clipped using bounding box. CRS: {new_raster.crs()}", 'vol test', Qgis.Info)

    # Set up raster calculator entries
    def create_raster_entry(raster, ref_name):
        raster_entry = QgsRasterCalculatorEntry()
        raster_entry.raster = raster
        raster_entry.bandNumber = 1
        raster_entry.ref = f"{ref_name}@1"
        return raster_entry

    old_raster_ref = create_raster_entry(old_raster, "oldRaster")
    new_raster_ref = create_raster_entry(new_raster, "newRaster")

    # Perform raster calculation (New Raster - Old Raster)
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
        if self.dlg.chkStats.isChecked():
            QgsMessageLog.logMessage("Saving statistics is checked", 'vol test', Qgis.Info)
            raster_diff = QgsProject.instance().mapLayersByName(r_name)
            if raster_diff:
                get_stats(self, raster_diff[0])
    else:
        QMessageBox.critical(self.dlg, "Error", "Raster calculation failed.")
        QgsMessageLog.logMessage("Raster calculation failed", 'vol test', Qgis.Critical)


def layout_report(self):
    layer = self.dlg.cmbLayoutPoints.currentLayer()
    attribute_name = self.dlg.cmbFieldValue.currentField()
    classification_method = self.dlg.cmbGradMeth.currentText()
    num_class = self.dlg.spbNumClass.value()
    sym_type = self.dlg.cmbSymType.currentText()

    graduated_symbology(self, layer, attribute_name, sym_type, classification_method, num_class)
    
    layoutName = self.dlg.lnLayoutName.text()
    if not layoutName:
         layoutName = "Report Layout"
    QgsMessageLog.logMessage(f"Layout {layoutName} being created", 'vol test', Qgis.Info)
    points = self.dlg.cmbLayoutPoints.currentLayer()
    #Adds a 10% buffer to the extent of the map so corner points are more visible
    extent = points.extent().buffered(points.extent().width()*0.1)
    run_layout(self, extent, layoutName)
    #raster_symbology(rasterDiff[0])
    QgsMessageLog.logMessage("Layout Created", 'vol test', Qgis.Info)

def create_text(layout, text, font_size, font = 'Times', bold = False, frame = True, HAlign = True, VAlign = True):
    txtbox = QgsLayoutItemLabel(layout)
    txtbox.setText(text)
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
     picture = QgsLayoutItemPicture(layout)
     picture.setPicturePath(filepath)
     picture.setId(idName)
     layout.addLayoutItem(picture)
     return picture

def map_single_point_with_labels(layout, feature, layer):
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

def create_monograph(self):
    layer = self.dlg.cmbMonoPoints.currentLayer()
    if not layer:
       QMessageBox.critical(self.dlg, "No Layer loaded", "Missing Point Layer")
       return
    #Get selected feature
    feature = self.dlg.cmbMonoFeat.feature()
    if not feature:
       QMessageBox.critical(self.dlg, "No Feature loaded", "Missing Point Feature")
       return
    #Get the name of the label
    feature_name = feature["label"]
    #Get descriptions
    target_color = self.dlg.txtTrgClr.toPlainText()
    target_description = self.dlg.txtTrgDscr.toPlainText()
    gnss_type = self.dlg.txtGnss.toPlainText()
    srvy_date = feature["survey_date"].toString('dd-MM-yy')
    layout_name = feature_name+'_'+srvy_date
    #Determine type of Cround Control Point
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
    title = create_text(layout, text = feature_name, font_size = 36)
    title.setFixedSize(QgsLayoutSize(97.5, 20))
    title.attemptMove(QgsLayoutPoint(7.5, y_pos, QgsUnitTypes.LayoutMillimeters))

    #Set Polimi headers
    polimi_text = "Politecnico di Milano\nDipartimento di Ingegneria Civile e Ambientale\nSezione di Geodesia e Geomatica"
    polimi = create_text(layout, polimi_text, font_size = 10, HAlign = False)
    polimi.setFixedSize(QgsLayoutSize(75, 20))
    polimi.attemptMove(QgsLayoutPoint(127.5, y_pos, QgsUnitTypes.LayoutMillimeters))
    polimi_path = self.dlg.lnLogo.text()
    polimi_logo = create_image(layout, polimi_path, 'PolimiLogo')
    polimi_logo.attemptMove(QgsLayoutPoint(105, y_pos, QgsUnitTypes.LayoutMillimeters))
    polimi_logo.setFixedSize(QgsLayoutSize(22.5,20))
    polimi_logo.setFrameEnabled(True)

    y_pos += polimi.boundingRect().height()

    #Add Descriptions
    dscr_text = f"Target: {target_color}\n\nDescrizione: {target_description}\nTipo di punto: {gcp_type}\n\nModalita di rilievo GNSS: {gnss_type}"
    dscr = create_text(layout, dscr_text, font_size = 12, VAlign = False, HAlign = False)
    dscr.setFixedSize(QgsLayoutSize(195, 50))
    dscr.setMarginX(0.5)
    dscr.attemptMove(QgsLayoutPoint(7.5, y_pos, QgsUnitTypes.LayoutMillimeters))
    y_pos += dscr.boundingRect().height()
    

    #Add Survey Title
    srvy_text = f"Coordinate {srvy_date}"
    srvy = create_text(layout, srvy_text, font_size = 12, bold = True)
    srvy.setFixedSize(QgsLayoutSize(195, 7.5))
    srvy.attemptMove(QgsLayoutPoint(7.5, y_pos, QgsUnitTypes.LayoutMillimeters))
    y_pos += srvy.boundingRect().height()

    #Create "Table" format for coordinates
    headers = ['X [m]', 'Y [m]', 'Z [m]', 'Lat (j)', 'Long (I)', 'H_ell [m]', 'Est [m]', 'Nord [m]']
    x_marg = 7.5
    col = 0
    for head in headers:
         lbl_txt = f"{head}"
         label = create_text(layout, lbl_txt, font_size=12)
         label.setFixedSize(QgsLayoutSize(24.1, 10))
         label.attemptMove(QgsLayoutPoint(x_marg, y_pos, QgsUnitTypes.LayoutMillimeters))
         x_marg += label.boundingRect().width()
    x_marg = 7.5
    for head in headers:
         val_obj = self.dlg.tblCoord.item(0,col)
         if col == 0:
            y_pos += label.boundingRect().height()
         if val_obj:
              val_txt = val_obj.text()
         else:
              val_txt = ' '         
         value = create_text(layout, val_txt, font_size = 12)
         value.setFixedSize(QgsLayoutSize(24.1, 10))
         value.attemptMove(QgsLayoutPoint(x_marg, y_pos, QgsUnitTypes.LayoutMillimeters))
         x_marg += label.boundingRect().width()
         col += 1
    y_pos += value.boundingRect().height()

    #Create Photo Title
    photo_txt = "ORTOFOTO"
    photo_title = create_text(layout, photo_txt, 12, bold = True)
    photo_title.setFixedSize(QgsLayoutSize(195,7.5))
    photo_title.attemptMove(QgsLayoutPoint(7.5, y_pos))
    y_pos += photo_title.boundingRect().height()

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

    ##Add Description Images
    #Upper right image
    photo_up_path = self.dlg.lnPhoto_1.text()
    photo_upper = create_image(layout, photo_up_path, 'PhotoUpper')
    photo_upper.attemptMove(QgsLayoutPoint(105, y_pos, QgsUnitTypes.LayoutMillimeters))
    photo_upper.setFixedSize(QgsLayoutSize(97.5,297-7.5-y_pos))
    photo_upper.setFrameEnabled(True)
    y_pos += photo_upper.boundingRect().height()
    #Lower right image
    photo_low_path = self.dlg.lnPhoto_2.text()
    photo_lower = create_image(layout, photo_low_path, 'PhotoLower')
    photo_lower.attemptMove(QgsLayoutPoint(105, y_pos, QgsUnitTypes.LayoutMillimeters))
    photo_lower.setFixedSize(QgsLayoutSize(97.5,297-7.5-y_pos))
    photo_lower.setFrameEnabled(True)

    #Open layout
    self.iface.openLayoutDesigner(layout)



                             
