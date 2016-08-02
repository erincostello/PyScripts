"""
Produces various output rasters for use in generating attribute rasters
and SSN models.
"""

# Import modules
from __future__ import print_function
import arcpy

# Check out Spatial Analyst
arcpy.CheckOutExtension("spatial")
from arcpy.sa import *
from arcpy import env

# if importing from base python instead of ArcGIS python copy the 
# ArcHydroTools.pth into the base python site packages folder
import ArcHydroTools

hydro_dir = r"F:\SSN_Test\hydro.gdb"

# True if the DEM will be aggregated to a different resolutiuon
agg = True

# Square km catchment size where streams initiate
# Assumes stream initiation at of 0.04 square km via Clarke et al 2008
# Aproximates 70% probability of being perennial
# Modeling Streams and Hydrogeomorphic attributes in Oregon from digital and field data.
stream_init_sqkm = 0.04
stream_init_sqm = stream_init_sqkm * 1000000

# Meters from the stream that defines the RSA
rsa_m = 30

# Spatial reference (This is not used here)
# NAD_1983_2011_Oregon_Statewide_Lambert_Ft_Intl
sr = arcpy.SpatialReference(6557)

env.workspace = hydro_dir
OUT_BE = env.workspace + "\\be"
OUT_BE_AGG = env.workspace + "\\be_agg"
OUT_FILL = env.workspace + "\\be_fill"


OUT_FDR  = env.workspace + "\\fdr"
OUT_FAC_ARCA = env.workspace + "\\fac_arca"
OUT_FAC_RCA =  env.workspace + "\\fac_rca"
OUT_FAC_RSA =  env.workspace + "\\fac_rsa"
OUT_FAC_ARSA =  env.workspace + "\\fac_arsa"

OUT_STREAM1 = env.workspace + "\\stream1"
OUT_STREAM2 = env.workspace + "\\stream2"
OUT_STREAM_SEG1 =  env.workspace + "\\streamseg"
OUT_STREAM_POLY = env.workspace + "\\stream_poly"
OUT_CATCHMENT = env.workspace + "\\catchment"
OUT_CATCHMENT_POLY  = env.workspace + "\\catchment_poly"
OUT_OUTLET_POINTS = env.workspace + "\\outlet_points"
OUT_JUNCTION_POINTS = env.workspace + "\\junction_points"
OUT_OUTLET_RASTER1 = env.workspace + "\\outlets1"
OUT_OUTLET_RASTER2 = env.workspace + "\\outlets2"
OUT_JUNCTION_RASTER1 = env.workspace + "\\junctions1"
OUT_JUNCTION_RASTER2 = env.workspace + "\\junctions2"
OUT_UP_AREA  = env.workspace + "\\up_area"
OUT_FDR_STREAM = env.workspace + "\\fdr_stream"
OUT_FDR_JUNCTION = env.workspace + "\\fdr_junction"
OUT_FDR_OUTLET = env.workspace + "\\fdr_outlet"
OUT_TO_DIVIDE =  env.workspace + "\\to_divide"
OUT_TO_STREAM1 = env.workspace + "\\to_stream_nd"
OUT_TO_STREAM2 = env.workspace + "\\to_stream"
OUT_RSA_WEIGHT = env.workspace + "\\rsa_weight"

OUT_TO_JUNCTION1  = env.workspace + "\\to_junction_nd"
OUT_TO_JUNCTION2  = env.workspace + "\\to_junction"
OUT_TO_OUTLET1  = env.workspace + "\\to_outlet_nd"
OUT_TO_OUTLET2  = env.workspace + "\\to_outlet"

# Reset geoprocessing environment settings
arcpy.ResetEnvironments()

#-- 1. Aggregate -------------------------
# this is only needed if we are downscaling from 3ft
if not arcpy.Exists(OUT_BE_AGG) and agg:
    print("elevation aggregate")
    BE_AGG = Aggregate(in_raster=OUT_BE, cell_factor=10, aggregation_type="MEAN")
    BE_AGG.save(OUT_BE_AGG)
    
    BE = Raster(OUT_BE_AGG)
    con_to_m = arcpy.Describe(BE).SpatialReference.metersPerUnit
    cell_size = arcpy.Describe(BE).meanCellWidth
    init_cells_sqkm = int(stream_init_sqkm / ((cell_size * con_to_m / 1000) ** 2))
    
    # Set env settings
    env.overwriteOutput = True
    env.cellSize = cell_size
    env.snapRaster = OUT_BE_AGG
    env.extent = OUT_BE_AGG
    env.mask = OUT_BE_AGG
    
elif agg:
    BE = Raster(OUT_BE_AGG)
    
    con_to_m = arcpy.Describe(BE).SpatialReference.metersPerUnit
    cell_size = arcpy.Describe(BE).meanCellWidth
    init_cells_sqkm = int(stream_init_sqkm / ((cell_size * con_to_m / 1000) ** 2))
    
    # Set env settings
    env.overwriteOutput = True
    env.cellSize = cell_size
    env.snapRaster = OUT_BE_AGG
    env.extent = OUT_BE_AGG
    env.mask = OUT_BE_AGG
    
else:
    BE = Raster(OUT_BE)

    con_to_m = arcpy.Describe(BE).SpatialReference.metersPerUnit
    cell_size = arcpy.Describe(BE).meanCellWidth
    init_cells_sqkm = int(stream_init_sqkm / ((cell_size * con_to_m / 1000) ** 2))
    
    # Set env settings
    env.overwriteOutput = True
    env.cellSize = cell_size
    env.snapRaster = OUT_BE
    env.extent = OUT_BE
    env.mask = OUT_BE_AGG

#-- 2. Fill -------------------------
if not arcpy.Exists(OUT_FILL):
    print("fill")
    ArcHydroTools.FillSinks(Input_DEM_Raster=BE,
                                   Output_Hydro_DEM_Raster=OUT_FILL)
FILL = Raster(OUT_FILL)


#-- 3. Flow Direction -------------------------    
if not arcpy.Exists(OUT_FDR):
    print("flow direction")
    
    ArcHydroTools.FlowDirection(FILL, OUT_FDR)
    
FDR = Raster(OUT_FDR)

# -- 4. Flow Accumulation  -------------------------
if not arcpy.Exists(OUT_FAC_ARCA):
    print("flow accumulation")
    ArcHydroTools.FlowAccumulation(FDR, OUT_FAC_ARCA)
        

FAC_ARCA = Raster(OUT_FAC_ARCA)

# -- 5. Stream Raster with NoData  -------------------------
if not arcpy.Exists(OUT_STREAM1):
    print("Stream Definition")
    ArcHydroTools.StreamDefinition(Input_Flow_Accumulation_Raster=FAC_ARCA,
                                   Number_of_cells_to_define_stream=init_cells_sqkm,
                                   Output_Stream_Raster=OUT_STREAM1,
                                   Area_Sqkm_to_define_stream=stream_init_sqkm)
STREAM1 = Raster(OUT_STREAM1)

# -- 6. Stream Raster excluding NoData -------------------------
if not arcpy.Exists(OUT_STREAM2):
    print("Stream NoData")
    STREAM2 = Con(in_conditional_raster=IsNull(STREAM1),
                       in_true_raster_or_constant=0, in_false_raster_or_constant=1)
    STREAM2.save(OUT_STREAM2)

else:
    STREAM2 = Raster(OUT_STREAM2)
    
# -- 7. Stream Segmentation -------------------------
if not arcpy.Exists(OUT_STREAM_SEG1):
    print("Stream Segmentation Raster") 
    #ArcHydroTools.StreamSegmentation(STREAM1, FAC_ARCA, OUT_STREAM_SEG1)
    STREAM_SEGS = StreamLink(STREAM1, FAC_ARCA)
    STREAM_SEGS.save(OUT_STREAM_SEG1)
else:
    STREAM_SEGS = Raster(OUT_STREAM_SEG1)

# -- 8. Stream Poly -------------------------
if not arcpy.Exists(OUT_STREAM_POLY):
    print("Stream Poly")
    ArcHydroTools.DrainageLineProcessing(Input_Stream_Link_Raster=STREAM_SEGS,
                                         Input_Flow_Direction_Raster=FDR,
                                         Output_Drainage_Line_Feature_Class=OUT_STREAM_POLY)
    
# -- 9. Catchment Raster -------------------------
if not arcpy.Exists(OUT_CATCHMENT):
    print("Catchment Raster")
    ArcHydroTools.CatchmentGridDelineation(Input_Flow_Direction_Raster=FDR, 
                                           Input_Link_Raster=STREAM_SEGS, 
                                           Output_Catchment_Raster=OUT_CATCHMENT)

CATCHMENT = Raster(OUT_CATCHMENT)

# -- 10. Catchment Poly -------------------------
if not arcpy.Exists(OUT_CATCHMENT_POLY):
    print("Catchment Poly")
    ArcHydroTools.CatchmentPolyProcessing(Input_Catchment_Raster=CATCHMENT, 
                                          Output_Catchment_Feature_Class=OUT_CATCHMENT_POLY)
    
# -- 11. Outlet Points -------------------------
if not arcpy.Exists(OUT_OUTLET_POINTS):
    print("Outlet Points")
    ArcHydroTools.DrainagePointProcessing(FAC_ARCA, 
                                          CATCHMENT, 
                                          OUT_CATCHMENT_POLY, 
                                          OUT_OUTLET_POINTS)

# -- 12. Outlet Raster with NoData -------------------------
if not arcpy.Exists(OUT_OUTLET_RASTER1):
    print("Outlet Points Raster1")
    arcpy.PointToRaster_conversion(in_features=OUT_OUTLET_POINTS, value_field="DrainID", 
                                  out_rasterdataset=OUT_OUTLET_RASTER1, 
                                  cell_assignment="MOST_FREQUENT",
                                  priority_field=None,
                                  cellsize=cell_size)        
OUTLETS1 = Raster(OUT_OUTLET_RASTER1)

# -- 13. Outlet Points Raster excluding NoData -------------------------
if not arcpy.Exists(OUT_OUTLET_RASTER2):
    print("Outlet Points Raster2")
    
    OUTLETS2 = Con(in_conditional_raster=IsNull(OUTLETS1),
                       in_true_raster_or_constant=0, in_false_raster_or_constant=1)
    OUTLETS2.save(OUT_OUTLET_RASTER2)
else:
    OUTLETS2 = Raster(OUT_OUTLET_RASTER2)

# -- 14. Upstream Area -------------------------
if not arcpy.Exists(OUT_UP_AREA):
    print("upstream area")
    
    # this will be in square meters
    UP_AREA = FAC_ARCA * ((cell_size * con_to_m)**2)
    UP_AREA.save(OUT_UP_AREA)
else:
    UP_AREA = Raster(OUT_UP_AREA)
    
# -- 15. Flow Direction w/ NULL streams  -------------------------
if not arcpy.Exists(OUT_FDR_STREAM):
    print("flow direction null streams")
    
    # square meters
    stream_init_sqm = stream_init_sqkm * 1000000              
                
    FDR_STREAM = SetNull(in_conditional_raster=((UP_AREA >= stream_init_sqm) | (STREAM2==1)),
                         in_false_raster_or_constant=FDR)          

    FDR_STREAM.save(OUT_FDR_STREAM)
else:
    FDR_STREAM = Raster(OUT_FDR_STREAM)
    
# -- 16. Flow Direction w/ NULL Outlets  -------------------------
if not arcpy.Exists(OUT_FDR_OUTLET):
    print("flow direction null outlets")
    
    FDR_OUTLET = SetNull(in_conditional_raster=(OUTLETS2==1),
                         in_false_raster_or_constant=FDR)          

    FDR_OUTLET.save(OUT_FDR_OUTLET)
else:
    FDR_OUTLET = Raster(OUT_FDR_OUTLET)
    

# -- 17. Flow Length to stream -------------------------
if not arcpy.Exists(OUT_TO_STREAM1):
    print("flow length to streams1")
    TO_STREAM1 = FlowLength(FDR_STREAM, "DOWNSTREAM") * con_to_m
    
    TO_STREAM1.save(OUT_TO_STREAM1)
else:
    TO_STREAM1 = Raster(OUT_TO_STREAM1)

if not arcpy.Exists(OUT_TO_STREAM2):
    print("flow length to streams2")
    # It's null at the stream so fix that
    TO_STREAM2 = Con(in_conditional_raster=((UP_AREA >= stream_init_sqm) | (STREAM2==1)),
                     in_true_raster_or_constant=0.0,
                     in_false_raster_or_constant=TO_STREAM1)           
    
    TO_STREAM2.save(OUT_TO_STREAM2)

else:
    TO_STREAM2 = Raster(OUT_TO_STREAM2)
    
# -- 18. Flow Length to Outlets -------------------------
if not arcpy.Exists(OUT_TO_OUTLET1):
    print("flow length to outlet1")
    TO_OUTLET1 = FlowLength(FDR_OUTLET, "DOWNSTREAM") * con_to_m
    
    TO_OUTLET1.save(OUT_TO_OUTLET1)

else:
    TO_OUTLET1 = Raster(OUT_TO_OUTLET1)
 
if not arcpy.Exists(OUT_TO_OUTLET2):
    print("flow length to outlet2")
    # It's null at the outlet point so fix that
    TO_OUTLET2 = Con(in_conditional_raster=IsNull(TO_OUTLET1),
                     in_true_raster_or_constant=0.0,
                     in_false_raster_or_constant=TO_OUTLET1)
    TO_OUTLET2.save(OUT_TO_OUTLET2)
    
else:
    TO_OUTLET2 = Raster(OUT_TO_OUTLET2) 
    
# -- 19. Make RSA weight raster -------------------------
if not arcpy.Exists(OUT_RSA_WEIGHT):
    print("RSA weight raster")
    
    RSA_WEIGHT = SetNull(in_conditional_raster=(TO_STREAM2 > rsa_m),
                         in_false_raster_or_constant=1)

    RSA_WEIGHT.save(OUT_RSA_WEIGHT)
else:
    RSA_WEIGHT = Raster(OUT_RSA_WEIGHT)


# -- 20. Make RCA FAC raster -------------------------
if not arcpy.Exists(OUT_FAC_RCA):
    print("RCA fac raster")
    
    FAC_RCA = FlowAccumulation(in_flow_direction_raster=FDR_OUTLET,
                                 data_type="FLOAT")

    FAC_RCA.save(OUT_FAC_RCA)
else:
    FAC_RCA = Raster(OUT_FAC_RCA)
    
# -- 21. Make RSA FAC raster -------------------------
if not arcpy.Exists(OUT_FAC_RSA):
    print("RSA fac raster")
    
    FAC_RSA = FlowAccumulation(in_flow_direction_raster=FDR_OUTLET,
                                 in_weight_raster=RSA_WEIGHT, 
                                 data_type="FLOAT")

    FAC_RSA.save(OUT_FAC_RSA)
else:
    FAC_RSA = Raster(OUT_FAC_RSA)
    
# -- 22. Make ARSA FAC raster -------------------------
if not arcpy.Exists(OUT_FAC_ARSA):
    print("ARSA fac raster")
    
    FAC_ARSA = FlowAccumulation(in_flow_direction_raster=FDR,
                                 in_weight_raster=RSA_WEIGHT, 
                                 data_type="FLOAT")

    FAC_ARSA.save(OUT_FAC_ARSA)
else:
    FAC_ARSA = Raster(OUT_FAC_ARSA)



# OLD-------------------------------------------------------------------
# -- 11. Junction Points  -------------------------
#if not arcpy.Exists(OUT_JUNCTION_POINTS):
    #arcpy.FeatureVerticesToPoints_management(in_features=OUT_STREAM_POLY,
                                             #out_feature_class=OUT_JUNCTION_POINTS,
                                              #point_location="END")    
    
## -- 12. Junction Points Raster with NoData -------------------------
#if not arcpy.Exists(OUT_JUNCTION_RASTER1):
        #print("Junction Points Raster1")
        #arcpy.PointToRaster_conversion(in_features=OUT_JUNCTION_POINTS, value_field="NextDownID", 
                                      #out_rasterdataset=OUT_JUNCTION_RASTER1, 
                                      #cell_assignment="MOST_FREQUENT",
                                      #priority_field=None,
                                      #cellsize=cell_size)        
#JUNCTIONS1 = Raster(OUT_JUNCTION_RASTER1)

## -- 13. Junctions Points Raster excluding NoData -------------------------
#if not arcpy.Exists(OUT_JUNCTION_RASTER2):
        #print("Junctions Points Raster2")
        
        #JUNCTIONS2 = Con(in_conditional_raster=IsNull(JUNCTIONS1),
                           #in_true_raster_or_constant=0, in_false_raster_or_constant=1)
        #JUNCTIONS2.save(OUT_JUNCTION_RASTER2)
#else:
    #JUNCTIONS2 = Raster(OUT_JUNCTION_RASTER2)

## -- 16. Flow Direction w/ NULL junctions  -------------------------
#if not arcpy.Exists(OUT_FDR_JUNCTION):
    #print("flow direction null junctions")
    
    #FDR_JUNCTION = SetNull(in_conditional_raster=(JUNCTIONS2==1),
                         #in_false_raster_or_constant=FDR)          

    #FDR_JUNCTION.save(OUT_FDR_JUNCTION)
#else:
    #FDR_JUNCTION = Raster(OUT_FDR_JUNCTION)
    
    ## -- Flow Length to Junctions -------------------------
    #if not arcpy.Exists(OUT_TO_JUNCTION1):
        #print("flow length to junction1")
        #TO_JUNCTION1 = FlowLength(FDR_JUNCTION, "DOWNSTREAM") * con_to_m
        
        #TO_JUNCTION1.save(OUT_TO_JUNCTION1)
    
    #else:
        #TO_JUNCTION1 = Raster(OUT_TO_JUNCTION1)
     
    #if not arcpy.Exists(OUT_TO_JUNCTION2):
        #print("flow length to junction2")
        ## It's null at the outlet point so fix that
        #TO_JUNCTION2 = Con(in_conditional_raster=IsNull(TO_JUNCTION1),
                         #in_true_raster_or_constant=0.0,
                         #in_false_raster_or_constant=TO_JUNCTION1)
        #TO_JUNCTION2.save(OUT_TO_JUNCTION2)
        
    #else:
        #TO_JUNCTION2 = Raster(OUT_TO_JUNCTION2)        
        
    