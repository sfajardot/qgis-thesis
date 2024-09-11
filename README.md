# qgis-thesis
Repository for the development of a QGIS plug-in for data processing in the Belvedere Glacier Project.

## Basic Information
Owner: Sebastián Fajardo Turner
University: Politecnico di Milano
Advisors: Federica Migliaccio, Federica Gaspari
Contact Information: sfajardoturner@gmail.com
Belvedere Glacier Project: https://thebelvedereglacier.it/

## The Overall Project
*Describe Belvedere Glacier Project here*

## Objective of the Thesis Project
In order to facilitate  analysis, a plug-in is being developed to automate the processing section of the data. Functionalities of the Plug-in are:

- Volume change of the glacier from DEMs ?
- Standardized map layouts for certain attributes ?
- Others ?

### Volume Change
The volume change functionality is part of the Processing Tab of the Plug-In. The basic process receives two overlapping Raster files from the user. It checks that both rasters are valid and in the same CRS, then proceeds to use the PyQGIS funtion QgsRasterCalculator to get the elevation difference between the 2. It returns to the map the raster file in GeoTiff format with the elevation difference by cell.

Additionally, the user can decide to use a vector polygon as a bounding box. In this case the plug-in uses the gdal processing function processing.cliprasterbymask. It clips both input raster files to the bounding box and proceeds with the elevation difference calculation.

Furthermore, the user can decide to save a Statistics file which is populated from the built-in function QgsRasterBandStats.

### Report Layout
To be added. Included in the second tab of the plug-in GUI. It aims to create standardized layouts to be included in reports. The user will be able to choose points in a vector format and select the attribute desired to be represented. The plug-in will then create a standardized layout for the attributes choses and potentially a graph from matplotlib.


