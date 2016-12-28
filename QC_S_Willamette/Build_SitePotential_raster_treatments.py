
from __future__ import print_function

import arcpy
from arcpy import env

from arcpy.sa import *
#from arcpy.sa import Con
#from arcpy.sa import Nibble
#from arcpy.sa import SetNull
arcpy.CheckOutExtension("Spatial")

working_dir = r"F:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Site_Potential_Geomorph.gdb"
env.workspace = working_dir

# This is the geomorph fc from the Willamette TMDL project files 
# clipped to the S. Willamette and reprojected into lambert (ogic)
geomorph_fc1 = r"geomorph_fc_s01_from_TMDL"
arcpy.env.extent = geomorph_fc1

out_raster1 = r"geomorph_treat_codes_s01"
out_raster2 = r"geomorph_treat_codes_s02"
out_raster3 = r"geomorph_treat_codes_s03_final"


# convert to raster
if not arcpy.Exists(out_raster1):
    arcpy.PolygonToRaster_conversion(geomorph_fc1, "GEOMORPH", out_raster1, "CELL_CENTER", "NONE" , 9)
else:
    raster1 = arcpy.Raster(out_raster1)

# make a null mask for the areas to use in the nibble
if not arcpy.Exists(out_raster2):
    print("set null")
    raster2 = arcpy.sa.SetNull(out_raster1,out_raster1,"VALUE IN (900, 2000, 3011)")
    raster2.save(out_raster2)
else:
    raster2 = arcpy.Raster(out_raster2)
        
# implement nearest neighbor on Qg2 (900) but keep water (2000, 3011) the same
if not arcpy.Exists(out_raster3):
    print("nearest neighbor nibble")
    raster3 = arcpy.sa.Con(out_raster1, out_raster1,
                           Nibble(out_raster1,
                                  out_raster2,
                                  "DATA_ONLY"),
                           "VALUE IN (2000, 3011)")
    raster3.save(out_raster3)
else:
    raster3 = arcpy.Raster(out_raster3)
    
print("done")