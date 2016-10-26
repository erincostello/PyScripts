
"""
This script generates disturbance rasters where disturbed=1 
if there is a lack of canopy within the specified period prior
to an index year.

A lack of canopy was identified using the Year of Disturbance (YOD) raster
(Kennedy et al 2010, Kennedy et al 2012) or the 2001 NLCD canopy cover
product (Huang et al 2001). The YOD raster identified the year in which
a forested area was disturbed by clearcut, fire, or other
processes between 1985 and 2008.

YOD was based on a change detection process so areas of both non-forest
and forest where no change was detected within the 1985-2008 study
period were not classified as disturbed by Kennedy et al (2010).
In these areas a lack of canopy was identified if the NLCD 2001 canopy
cover product (Huang et al 2001) classified the percent canopy cover
as being between 0 and 10 percent. This was interpreted as an area
having minimal canopy cover that did not change status between
1985 and 2008.

Huang, C., Yang, L., Wylie, B., and Homer, C. 2001. A strategy for
estimating tree canopy density using landsat & ETM+ and high resolution
images over large areas, The proceedings of the Third International
Conference on Geospatial Information in Agriculture and
Forestry held in Denver, Colorado, 5-7 November, 2001, 1 disk. 

Kennedy, R.E., Yang, Z., Cohen W.B. 2010. Detecting trends in forest
disturbance and recovery using yearly Landsat time series:
1. LandTrendr - temporal segmentation algorithms. Remote Sensing of
Environment. 114(12): 2897-2910.

Kennedy, R.E., Yang, Z., Cohen W.B., Pfaff, E., Braaten, J. Nelson, P.
2012. Spatial and temporal patterns of forest disturbance and regrowth
within the area of the Northwest Forest Plan. Remote Sensing of
Environment. 122: 117-133.
    
YOD data accessed here:
ftp://ftp.fsl.orst.edu/pub/landtrendr/nwfp_disturbance_03012011/

"""

# Import modules
from __future__ import print_function
import arcpy
from arcpy import env

# Check out Spatial Analyst
arcpy.CheckOutExtension("spatial")
from arcpy.sa import *


work_dir = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\Disturbance.gdb"
env.workspace = work_dir

# These rasters are in the same projection and clipped to the study area
path_yod = env.workspace + "\\landtrendr_R03012011_yod1_ssn"
path_nlcd = env.workspace + "\\NLCD_2001_canopy_ssn"

# number of years prior to the index year to be classified
# as disturbed.
d_periods = [1, 3, 10]

# the index years 
years = range(1996, 2009, 1)

YOD = Raster(path_yod)
NLCD = Raster(path_nlcd)
out_disturb1 = env.workspace + "\\Disturbance_ssn"

# Set env settings
env.overwriteOutput = True
env.cellSize = path_nlcd
env.snapRaster = path_nlcd
env.extent = path_nlcd

# -- Combine YOD and NLCD
if not arcpy.Exists(out_disturb1):
    print("combine YOD and NLCD")
    
    # YOD = 0 means it was not classifed because there was no change
    DISTURB1 = Con(YOD == 0,
                       in_true_raster_or_constant=NLCD,
                       in_false_raster_or_constant=YOD)    

    DISTURB1.save(out_disturb1)
    
else:
    DISTURB1 = Raster(out_disturb1)

for year in years:
    for d_period in d_periods:
        
        out_disturb2 = "DISTURB_{0}yr_{1}".format(d_period, year)
        if not arcpy.Exists(out_disturb2):
            print("processing {0}".format(out_disturb2))
            
            rc_table = RemapRange([[0, 10, 1],
                                   [10, 100, "NODATA"],
                                   [1984, year - d_period, "NODATA"], 
                                   [year - d_period, year, 1],
                                   [year, 2009, "NODATA"]
                                   ])
        
            DISTURB2 = Reclassify(in_raster=DISTURB1,
                                  reclass_field="Value",
                                  remap=rc_table, 
                                  missing_values="NODATA")
            
            DISTURB2.save(out_disturb2)


