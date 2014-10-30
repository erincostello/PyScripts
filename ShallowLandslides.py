#------------------------------------------------------------------------------------------
# ShallowLandslide_py v2.31
#
# PURPOSE
# This script generates a shallow landslide susceptibility raster using
# morphometric analysis of slope, landform, and lithology. The methods used here follow
# those described by Shaw and Johnson (1995).  Calibration and parameterization was
# based on landslide inventory data collected by Robinson et al (1999).
#
# Output landslide susceptibility reflects the susceptibility that may occur under similar
# landscape and precipitation conditions observed in the study areas.
# The landslide inventory data used to calibrate this model was collected after
# the 1996/97 Oregon rainstorms where the minimum, maximum, and mean 24 hour
# precipitation was 2.9 inches, 11.7 inches, and 6.9 inches respectively. This equates to
# approximately 51%, 110% and 81% of the 24 hour 100 year precipitation event.
#
#
# REQUIREMENTS
# Python 2.7.2, ArGIS arcpy, and Spatial analyst
# Use of LiDAR data is highly reccommended.
#
# CONTACT
# Ryan Michie, michie.ryan@deq.state.or.us
# Oregon Department of Environmental Quality
# 
#------------------------------------------------------------------------------------------

# Import modules
import arcpy
import os
import time
from arcpy import env

# Check out Spatial Analyst
arcpy.CheckOutExtension("spatial")
from arcpy.sa import *

# INPUT FILES
isLiDAR = True
DEM_raster_input = "C:\\WorkSpace\\Biocriteria\\WatershedCharaterization\\BareEarth_Prob.gdb\\be_prob"
FSP_raster_input = "C:\\WorkSpace\\Biocriteria\\WatershedCharaterization\\Lithology.gdb\\Lithology_ws_FSP"
Slope_Reclassification_Table = "C:\\WorkSpace\\Biocriteria\\WatershedCharaterization\\ShallowLandslides\\Reclass_Tables_v3\\slope_relcass_v3"
Lith_Reclassification_Table = "C:\\WorkSpace\\Biocriteria\\WatershedCharaterization\\ShallowLandslides\\Reclass_Tables_v3\\lithology_reclass_v3"
Plan_Reclassification_Table1 = "C:\\WorkSpace\\Biocriteria\\WatershedCharaterization\\ShallowLandslides\\Reclass_Tables_v3\\planform_reclass_LiDAR_v3"
Plan_Reclassification_Table2 = "C:\\WorkSpace\\Biocriteria\\WatershedCharaterization\\ShallowLandslides\\Reclass_Tables_v3\\planform_reclass_dem10m_v3"
Susceptability_Reclassification_Table = "C:\\WorkSpace\\Biocriteria\\WatershedCharaterization\\ShallowLandslides\\Reclass_Tables_v3\\susceptibility_reclass_v3"

# OUTPUT FILES
env.workspace = "C:\\WorkSpace\\Biocriteria\\WatershedCharaterization\\ShallowLandslides\\ShallowLandslides_OUT_LiDAR_prob.gdb"
#env.workspace = "C:\\WorkSpace\\Biocriteria\\WatershedCharaterization\\ShallowLandslides\\ShallowLandslides_OUT_dem10m.gdb"
OUT_SUSCEP = env.workspace + "\\SUSCEP"
OUT_SUSCEP_reclass = env.workspace + "\\SUSCEP_reclass_Final"
OUT_SLOPE = env.workspace + "\\SLOPE"
OUT_SLOPE_reclass = env.workspace + "\\SLOPE_reclass"
OUT_LITH_reclass = env.workspace + "\\LITH_reclass"
OUT_PROFILE = env.workspace + "\\PROFILE"
OUT_CURVE = env.workspace + "\\CURVE"
OUT_PLAN = env.workspace + "\\PLAN"
OUT_PLAN_Focal = env.workspace + "\\PLAN_Focal"
OUT_PLAN_reclass = env.workspace + "\\PLAN_reclass"

# OUTPUT FILES THAT MAY ALREADY EXIST BUT NOT IN env.workspace
# OUT_SLOPE = "C:\\WorkSpace\\Biocriteria\\WatershedCharaterization\\BareEarth_all.gdb\\be_all"

###########################
# Set env settings
env.overwriteOutput = True
env.cellSize = DEM_raster_input
env.snapRaster = DEM_raster_input

###########################
# keeping track of time
startTime= time.time()
print "START ShallowLandslide_py v2.3: %s" % (time.ctime(startTime))

###########################
# 1. Landform shape, use Planform only

print "Starting process 1/8: Generate Planform Curvature"
if arcpy.Exists(OUT_PLAN) == False:
        CURVE = Curvature(DEM_raster_input, 1.0, OUT_PROFILE, OUT_PLAN)
        CURVE.save(OUT_CURVE)
else:
        OUT_PLAN = Raster(OUT_PLAN)
        print "PLAN raster exists"
        
###########################
# 2. Perform a focal mean on Planform Curvature

print "Starting process 2/8: Focal statistics on Planform Curvature"
if arcpy.Exists(OUT_PLAN_Focal) == False:
        if isLiDAR == True:
                # This assumes a 3 ft / 1 meter cell resolution. (15 foot rectangle neighborhood window)
                PLAN_Focal = FocalStatistics(OUT_PLAN, NbrRectangle(5, 5, "CELL"), "MEAN", "DATA")
                PLAN_Focal.save(OUT_PLAN_Focal)
        else:
                print "10m DEM, skipping focal statistics"
                PLAN_Focal = Raster(OUT_PLAN)
else:
        PLAN_Focal = Raster(OUT_PLAN_Focal)
        print "PLAN_focal raster exists"
        
###########################
# 3. Reclassify PLAN
print "Starting process 3/8: Reclassify PLAN"

if isLiDAR == True:
        Plan_Reclassification_Table = Plan_Reclassification_Table1
else:
        Plan_Reclassification_Table = Plan_Reclassification_Table2
        

if arcpy.Exists(OUT_PLAN_reclass) == False:
        PLAN_reclass = ReclassByTable(PLAN_Focal, Plan_Reclassification_Table, "FROM", "TO", "OUT", "DATA")
        PLAN_reclass.save(OUT_PLAN_reclass)
else:
        PLAN_reclass = OUT_PLAN_reclass
        print "PLAN_reclass raster exists"

###########################
# 4. Reclassify LITH
print "Starting process 4/8: Reclassify LITH"
if arcpy.Exists(OUT_LITH_reclass) == False:
        LITH_reclass = ReclassByTable(FSP_raster_input, Lith_Reclassification_Table, "FROM", "TO", "OUT", "DATA")
        LITH_reclass.save(OUT_LITH_reclass)
else:
        LITH_reclass = Raster(OUT_LITH_reclass)
        print "LITH_reclass raster exists"
        
###########################
# 5. Slope
print "Starting process 5/8: Slope"
if arcpy.Exists(OUT_SLOPE) == False:
        SLOPE = Slope(DEM_raster_input, "PERCENT_RISE", 1.0)
        SLOPE.save(OUT_SLOPE)
else:
        SLOPE = Raster(OUT_SLOPE)
        print "SLOPE raster exists"

###########################
# 6. Reclassify SLOPE
print "Starting process 6/8: Reclassify SLOPE"
if arcpy.Exists(OUT_SLOPE_reclass) == False:
        SLOPE_reclass = ReclassByTable(SLOPE, Slope_Reclassification_Table, "FROM", "TO", "OUT", "DATA")
        SLOPE_reclass.save(OUT_SLOPE_reclass)
else:
        SLOPE_reclass = Raster(OUT_SLOPE_reclass)
        print "SLOPE_reclass raster exists"
        
###########################
# 7. Build Raster Codes for SUSCEP (Plus)
print "Starting process 7/8: Calculate SUSCEP Raster Codes (Plus)"
if arcpy.Exists(OUT_SUSCEP) == False:
        SUSCEP = (LITH_reclass + SLOPE_reclass + PLAN_reclass)
        SUSCEP.save(OUT_SUSCEP)
        # In arcgis use raster calculator:
        # arcpy.gp.RasterCalculator_sa("\"%LITH_reclass%\" + \"%SLOPE_reclass%\" + \"%PLAN_reclass%\"", SUSCEP) 
else:
        SUSCEP = Raster(OUT_SUSCEP)
        print "SUSCEP raster exists"

###########################
# 8. Reclassify SUSCEP
print "Starting process 8/8: Reclassify SUSCEP"
SUSCEP_relcass = ReclassByTable(SUSCEP, Susceptability_Reclassification_Table, "FROM", "TO", "OUT", "DATA")
SUSCEP_relcass.save(OUT_SUSCEP_reclass)

endTime = time.time()
Elapsed_MIN = (endTime - startTime) / 60
print "All processes complete in %s minutes" % (Elapsed_MIN)
print "END ShallowLandslide_py v2.3: %s" % (time.ctime(endTime))
