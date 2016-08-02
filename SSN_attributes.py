"""
Produces RSA, ARSA, RCA, and ARCA output rasters for an input attribute.
Note that catchment outlet on the RSA and RCA rasters will be NULL.
"""

# Import modules
from __future__ import print_function
import arcpy

# Check out Spatial Analyst
arcpy.CheckOutExtension("spatial")
from arcpy.sa import *
from arcpy import env

hydro_dir = r"F:\SSN_Test\hydro.gdb"

attr_dir = r"F:\SSN_Test\attrbutes.gdb"

# name of the starting attribute raster
attr_name = "disturb"

env.workspace = hydro_dir
OUT_FAC_RCA =  env.workspace + "\\fac_rca"
OUT_FAC_RSA =  env.workspace + "\\fac_rsa"
OUT_FAC_ARCA = env.workspace + "\\fac_arca"
OUT_FAC_ARSA =  env.workspace + "\\fac_arsa"

env.workspace = attr_dir
ATTR = Raster(env.workspace + "\\"+ attr_name)
OUT_ATTR_RSA = env.workspace + "\\" + attr_name + "_rsa"
OUT_ATTR_RCA = env.workspace + "\\" + attr_name + "_rca"
OUT_ATTR_ARCA = env.workspace + "\\" + attr_name + "_arca"
OUT_ATTR_ARSA = env.workspace + "\\" + attr_name + "_arsa"

# Set env settings
env.overwriteOutput = True
env.cellSize = cell_size
env.snapRaster = OUT_BE_AGG
env.extent = OUT_BE_AGG
env.mask = OUT_BE_AGG

def accumulate(attr_raster, fac_raster, fdr_raster, weight=1):
    """
    Accumulates the attribute raster
    """
    attr_accum = FlowAccumulation(in_flow_direction_raster=fdr_raster,
                                  in_weight_raster=(attr_raster*weight), 
                                  data_type="FLOAT")
    
    return attr_accum / fac_raster

# -- RCA -----------------------------------------
if not arcpy.Exists(OUT_ATTR_RCA):
    ATTR_ARSA = accumulate(var_raster=ATTR,
                           fac_raster=FAC_RCA,
                           fdr_raster=FDR_OUTLET,
                           weight=1)
    ATTR_ARSA.save(OUT_ATTR_RCA)

# -- ARCA -----------------------------------------
if not arcpy.Exists(OUT_ATTR_ARCA):
    ATTR_ARCA = accumulate(var_raster=ATTR,
                           fac_raster=FAC,
                           fdr_raster=FDR,
                           weight=1)
    ATTR_ARCA.save(OUT_ATTR_ARCA)

# -- RSA -----------------------------------------
if not arcpy.Exists(OUT_ATTR_RSA):
    ATTR_ARSA = accumulate(var_raster=ATTR,
                           fac_raster=FAC_RSA,
                           fdr_raster=FDR_OUTLET,
                           weight=RSA_WEIGHT)
    ATTR_ARSA.save(OUT_ATTR_RSA)

# -- ARSA -----------------------------------------
if not arcpy.Exists(OUT_ATTR_ARSA):
    ATTR_ARSA = accumulate(var_raster=ATTR,
                           fac_raster=FAC_ARSA,
                           fdr_raster=FDR,
                           weight=RSA_WEIGHT)
    ATTR_RSA.save(OUT_ATTR_ARSA)

print("done")