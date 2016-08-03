"""
Produces RSA, ARSA, RCA, and ARCA output rasters for an input attribute.
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
attr_name = "disturb_agg"

env.workspace = hydro_dir
FAC_RCA =  Raster(env.workspace + "\\fac_rca")
FAC_RSA =  Raster(env.workspace + "\\fac_rsa")
FAC_ARCA = Raster(env.workspace + "\\fac_arca")
FAC_ARSA =  Raster(env.workspace + "\\fac_arsa")
FDR = Raster(env.workspace + "\\fdr")
FDR_RSA = Raster(env.workspace + "\\fdr_euc")
FDR_OUTLET = Raster(env.workspace + "\\fdr_outlet")
FDR_RSA_OUTLET = Raster(env.workspace + "\\fdr_euc_outlet")
RSA_WEIGHT = Raster(env.workspace + "\\rsa_euc_weight")
OUTLETS = Raster(env.workspace + "\\outlets2")
CATCHMENT = Raster(env.workspace + "\\catchment")
RSA_ZONES = Raster(env.workspace + "\\rsa_euc_zone")

env.workspace = attr_dir
attr_path =  env.workspace + "\\"+ attr_name
ATTR = Raster(attr_path)
OUT_ATTR_RSA = env.workspace + "\\" + attr_name + "_rsa"
OUT_ATTR_RCA = env.workspace + "\\" + attr_name + "_rca"
OUT_ATTR_ARCA = env.workspace + "\\" + attr_name + "_arca"
OUT_ATTR_ARSA = env.workspace + "\\" + attr_name + "_arsa"

# Set env settings
cell_size = arcpy.Describe(attr_path).meanCellWidth

env.overwriteOutput = True
env.cellSize = cell_size
env.snapRaster = attr_path
env.extent = attr_path
env.mask = attr_path

def accumulate(attr_raster, fac_raster, fdr_raster, weight=1,
               fill_outlets=False, catchment_raster=None,
               outlet_raster=None):
    """
    Accumulates the attribute raster
    """
    attr_sum = Plus(FlowAccumulation(in_flow_direction_raster=fdr_raster,
                                     in_weight_raster=Times(attr_raster, weight), 
                                     data_type="FLOAT"),
                    attr_raster)
    attr_accum = Divide(attr_sum, fac_raster)
    
    if fill_outlets:
        zonal_raster = ZonalStatistics(in_zone_data=catchment_raster,
                                       zone_field="Value",
                                       in_value_raster=attr_raster,
                                       statistics_type="MEAN",
                                       ignore_nodata="DATA")
        
        return Con(in_conditional_raster=(outlet_raster==1),
                         in_true_raster_or_constant=zonal_raster,
                         in_false_raster_or_constant=attr_accum)
    else:
        return attr_accum


# -- RCA -----------------------------------------
if not arcpy.Exists(OUT_ATTR_RCA):
    print("{0} RCA".format(attr_name))
    ATTR_ARSA = accumulate(attr_raster=ATTR,
                           fac_raster=FAC_RCA,
                           fdr_raster=FDR_OUTLET,
                           weight=1, fill_outlets=True,
                           catchment_raster=CATCHMENT,
                           outlet_raster=OUTLETS)
    
    ATTR_ARSA.save(OUT_ATTR_RCA)

# -- ARCA -----------------------------------------
if not arcpy.Exists(OUT_ATTR_ARCA):
    print("{0} ARCA".format(attr_name))
    ATTR_ARCA = accumulate(attr_raster=ATTR,
                           fac_raster=FAC_ARCA,
                           fdr_raster=FDR,
                           weight=1)
    ATTR_ARCA.save(OUT_ATTR_ARCA)

# -- RSA -----------------------------------------
if not arcpy.Exists(OUT_ATTR_RSA):
    print("{0} RSA".format(attr_name))
    ATTR_ARSA = accumulate(attr_raster=ATTR,
                           fac_raster=FAC_RSA,
                           fdr_raster=FDR_RSA_OUTLET,
                           weight=RSA_WEIGHT, fill_outlets=True,
                           catchment_raster=RSA_ZONES,
                           outlet_raster=OUTLETS)
    ATTR_ARSA.save(OUT_ATTR_RSA)

# -- ARSA -----------------------------------------
if not arcpy.Exists(OUT_ATTR_ARSA):
    print("{0} ARSA".format(attr_name))
    ATTR_ARSA = accumulate(attr_raster=ATTR,
                           fac_raster=FAC_ARSA,
                           fdr_raster=FDR_RSA,
                           weight=RSA_WEIGHT)
    ATTR_ARSA.save(OUT_ATTR_ARSA)

print("done")