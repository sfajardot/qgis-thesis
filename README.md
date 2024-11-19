# qgis-thesis
Repository for the development of a QGIS plug-in for glacier data processing, including elevation/volume change based on raster files, interpolation and symbology based on points, and GCP monographies.

## Basic Information
Owner: Sebastián Fajardo Turner
University: Politecnico di Milano
Advisors: Federica Migliaccio, Federica Gaspari
Contact Information: sfajardoturner@gmail.com
Belvedere Glacier Project: https://thebelvedereglacier.it/

## The Overall Project
This thesis presents the design and implementation of a QGIS plugin aimed at 
facilitating glacier monitoring, specifically focusing on the Belvedere Glacier in the 
Italian Alps. The plugin is designed to streamline and automate essential analysis 
processes, including elevation and volume change detection, displacement and surface 
velocity mapping, and the generation of Ground Control Point reports. The motivation 
behind this work stems from the need to simplify and standardize the data processing 
workflows that follow annual glacier survey campaigns, enabling wider accessibility 
to glacier data analysis while reducing the required expertise and time commitment. 
The methodology consists in integrating geospatial data from Digital Surface Models 
and Ground Control Point measurements into the QGIS environment, providing a 
user-friendly interface that supports tasks such as calculating glacier volume changes 
and applying symbolism to visualize displacement and surface velocity. The plugin's 
core functionalities—automatic interpolation of glacier surface changes and the 
creation of standardized monographs for GCPs—were tested using data from the 
Belvedere Glacier monitoring project, providing an efficient solution for the long-term 
sustainability of the research program. 
The results demonstrate the plugin’s ability to significantly reduce the time required 
to analyze glacier dynamics while ensuring consistent and reliable outputs. In 
particular, the plugin has proven useful in visualizing trends in glacier displacement, 
surface velocity, and acceleration. These insights are crucial for understanding the 
glacier’s response to climate change and evaluating potential hazards like glacier 
surges or collapses. The plugin’s open-source nature ensures it can be adapted for 
other glaciers and contexts, making it a versatile tool for the glaciological community. 
Its application extends beyond research, providing an educational platform for 
students and a practical tool for professionals in glacier monitoring. 

## Objective of the Thesis Project
Currently, the processing operations for volume change and velocity interpolations in QGIS are manually carried out, as well as the map report layouts, which convey disaggregated steps. A QGIS plugin or script could automate these steps, leading to time-saving and standardized outputs.
The primary objective of this thesis is to develop an open-source QGIS plugin designed to streamline and automate key processes in glacier monitoring, making it accessible and useful for any glacier monitoring program worldwide. The goal is to create a versatile tool that can be easily adapted and applied to other glacier systems. Nonetheless, the plugin has been developed using the Belvedere Glacier monitoring project as a baseline, therefore, it will be the focus of the discussion of this project. The plugin aims to address several inefficiencies in current monitoring workflows, which often involve manual data processing, inconsistent reporting, and visualization challenges. The main objectives are as follows:
1.	Automation of DSM Elevation Change Calculation: The plugin automates the comparison of Digital Surface Models (DSMs) to track changes in glacier surface elevation over time. This process, which is typically performed manually, is time-consuming and error prone. By automating the calculation of elevation changes between two DSMs and allowing users to apply spatial constraints (such as bounding boxes), the plugin significantly improves the efficiency and accuracy of glacier surface change analysis, facilitating rapid and standardized data processing.
2.	Interpolation of Values from Point Layers: Glacier monitoring often involves tracking surface velocity, displacement, or other point-based data (e.g., GNSS measurements). The plugin automates the interpolation of values from these point layers, providing a clearer picture of glacier behavior over time. This feature speeds up the analysis process and improves the accuracy of the understanding of the glacier’s evolution, making it a valuable tool for both researchers and practitioners involved in glacier dynamics studies.
3.	Standardization of Ground Control Point (GCP) Report Layouts: Ground Control Points are critical for long-term monitoring of glaciers. The plugin automates the creation of standardized GCP report layouts, ensuring consistent and repeatable outputs across multiple years and campaigns. This standardization reduces the risk of human error and allows for more reliable data comparisons, making it easier to maintain high-quality records for long-term glacier monitoring.
4.	Advanced Symbology for Visualizing Glacier Data: The plugin includes an intuitive symbology option in the interpolation tab, which allows users to apply advanced symbology techniques to visualize glacier data. For example, users can apply graduated symbology to represent velocity fields or vector field markers to visualize glacier displacement. By improving the visual representation of complex datasets, the symbology feature enhances the interpretation and communication of glacier behavior.
5.	Open-Source Accessibility and Adaptability: A key objective of this plugin is to ensure that it is accessible to all glacier monitoring programs globally. By making the plugin open source, it encourages collaboration, adaptation, and widespread use in glacier monitoring projects beyond the initial case of the Belvedere Glacier. The tool’s modular design and adaptability mean it can be customized to suit different glacier environments, making it a practical solution for diverse research teams and field conditions.
The development of this open-source plugin will significantly improve the workflow efficiency of glacier monitoring efforts, reduce manual errors, and ensure standardized outputs. By providing a freely accessible tool for the broader glacier monitoring community, the plugin has the potential to become a valuable resource for both researchers and practitioners in cryosphere studies.


### Volume Change
The main purpose of this plugin feature is to calculate elevation changes between two DSMs (Digital Surface Models), which is a key metric in glacier monitoring. By analyzing changes in surface elevation over time, researchers can observe glacier dynamics, track mass loss or gain, and identify patterns of retreat or advance. It is important to note that this feature does not provide the glacier’s total mass; rather, it estimates elevation changes between two time periods by performing a raster calculation. Additionally, users have the option to select a checkbox to display the result as a volume change instead of an elevation change. When this option is chosen, the plugin multiplies the elevation change by each pixel's surface area to estimate volume change. 

### Interpolation and Symbology
The Interpolation and Symbology tab is divided into two main processes. The core process is the interpolation of an attribute field within a point vector layer. Applying symbology is an optional functionality provided. Using this tab, the user can create interpolated raster surfaces from point data, which is essential in glacier monitoring for estimating values such as displacement velocity, temperature, or snow depth over an area based on limited point measurements. This function uses two common interpolation methods—Inverse Distance Weighting (IDW) and Triangular Irregular Networks (TIN)—allowing the user to generate a continuous surface from discrete data points. The interpolated raster can help researchers visualize spatial variations across the glacier and fill in gaps where direct measurements were not taken. 
Furthermore, the user may choose to complement the visualization of the interpolation by applying symbology to the points which were used to interpolate the field. This helps to generate a more robust and understandable map which portrays the behavior of the glacier.  

### Monography of GCPs
This section is dedicated to the generation of monographies in the layout using Ground Control Points (GCPs). Monographies are standardized, detailed reports designed to provide essential information about GCPs, which play a critical role in the accuracy of geospatial data and analysis. In the specific case of glacier monitoring, accurate GCP data is crucial for anchoring spatial measurements and ensuring that datasets remain consistent over time. Furthermore, in the case of the Belvedere Glacier, there are points within the glacier that move following the glacier’s dynamics, thus finding differences in positions and keeping track on where they are for future data collection is relevant. 


