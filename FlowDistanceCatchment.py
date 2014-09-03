#######################################################################################
# FlowDistanceCatchment_py v1.0
# 
# This script will take an input flow direction raster and watershed catchment raster
# where each unique catchment has a unique ID and output a flow length raster measured 
# in the downstream direction for the enitre flow direction extent, and a flow length 
# raster measured in the upstream direction from the most downstream point in each 
# watershed catchment.
#
# Ryan Michie
#######################################################################################

# Import system modules
from __future__ import print_function
import arcpy, os, time
import arcpy
from arcpy import env

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")
from arcpy.sa import *

# INPUT FILES
FAC = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\Hydro.gdb\FAC_nhdplusv21_ssn"
FDR = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\Hydro.gdb\FDR_nhdplusv21_ssn"
#CATCHMENT = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\Stations.gdb\Stations_ssn_watersheds"
CATCHMENT = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\LSN03\Catchment_RIDs.gdb\Catchment_RID_30m"
CATCHMENT_zone_field = "RID"

# OUTPUT FILES
env.workspace = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\Hydro.gdb"
OUT_FLds = env.workspace + "\\FLds"
OUT_FLds_minimum = env.workspace + "\\FLds_min_by" + CATCHMENT_zone_field
OUT_FLus = env.workspace + "\\FLus_by"  + CATCHMENT_zone_field

###########################
# Set env settings
env.overwriteOutput = True
env.cellSize = FDR
env.snapRaster = FDR

try:
   
    ###########################
    # keeping track of time
    startTime= time.time()
    print("START FlowDistanceCatchment_py v1.0: %s" % (time.ctime(startTime)))
    
    ###########################
    # 1. Flow Length in the downstream direction
    
    print("Starting process 1/3: Generate flow length in the downstream direction")
    if arcpy.Exists(OUT_FLds) == False:
        FLds = FlowLength(FDR, "DOWNSTREAM", "")
        FLds.save(OUT_CURVE)
    else:
        FLds = Raster(OUT_FLds)
        print("Flow length raster exists")
    
    ###########################
    # 2. Find Minimum flow length for each catchment and output as a raster
    
    print("Starting process 2/3: Find Minimum Flow Length for each Catchment")
    if arcpy.Exists(OUT_FLds_minimum) == False:
        FLds_minimum = ZonalStatistics(CATCHMENT, CATCHMENT_zone_field, FLds, "MINIMUM")
        FLds_minimum.save(OUT_FLds_minimum)
    else:
        FLds_minimum = Raster(OUT_FLds_minimum)
        print("Minimum flow length raster by catchment exists")
    
    ###########################
    # 3 Calculate Flow Length upstream from the bottom of each catchement using Minus
    
    print("Starting process 3/3: Calculating flow length from the bottom of each catchement")
    if arcpy.Exists(OUT_FLus) == False:
        FLus = Minus(FLds, FLds_minimum)
        FLus.save(OUT_FLus)
    else:
        print("Final output raster exists")
    
    endTime = time.time()
    Elapsed_MIN = (endTime - startTime) / 60
    print("All processes complete in %s minutes" % (Elapsed_MIN))
    print("END FlowDistanceCatchment_py v1.0: %s" % (time.ctime(endTime)))    

# For arctool errors
except arcpy.ExecuteError:
    msgs = arcpy.GetMessages(2)
    print(msgs)

# For other errors
except:
    import traceback, sys
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    print(pymsg)
    print(msgs)