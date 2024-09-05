from qgis.PyQt.QtGui import QColor
from qgis.core import Qgis, QgsProject, QgsPrintLayout, QgsMessageLog, QgsLayoutItemMap, QgsLayoutPoint, \
     QgsUnitTypes, QgsApplication, QgsLayoutItemPage, QgsRasterBandStats, QgsColorRampShader,\
     QgsRasterShader, QgsSingleBandPseudoColorRenderer

from PyQt5.QtWidgets import  QMessageBox

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


                             
