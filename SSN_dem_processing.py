"""
Produces various output rasters for use in generating attribute rasters
and SSN models.
"""

# Import modules
from __future__ import print_function
import arcpy

import time

# Check out Spatial Analyst
arcpy.CheckOutExtension("spatial")
from arcpy.sa import *
from arcpy import env

# if importing from base python instead of ArcGIS python copy the 
# ArcHydroTools.pth into the base python site packages folder
import ArcHydroTools

# output directory for the hydro outputs
#hydro_dir = r"F:\SSN_Test\hydro_burn.gdb"
#hydro_dir = r"F:\WorkSpace\Mid_Coast\Hydro\Salmon.gdb"
#hydro_dir = r"F:\WorkSpace\Mid_Coast\Hydro\Devils_Lake_Frontal.gdb"
#hydro_dir = r"F:\WorkSpace\Mid_Coast\Hydro\Siletz.gdb"
#hydro_dir = r"F:\WorkSpace\Mid_Coast\Hydro\Yaquina.gdb"
#hydro_dir = r"F:\WorkSpace\Mid_Coast\Hydro\Beaver_Creek.gdb"
#hydro_dir = r"F:\WorkSpace\Mid_Coast\Hydro\Alsea.gdb"
hydro_dir = r"F:\WorkSpace\Mid_Coast\Hydro\Alsea_Frontals.gdb"
#hydro_dir = r"F:\WorkSpace\Mid_Coast\Hydro\Siuslaw.gdb"
#hydro_dir = r"F:\WorkSpace\Mid_Coast\Hydro\Siltcoos.gdb"

# True if the DEM will be aggregated to a different resolutiuon
agg = True
agg_factor = 5

make_sinks = False

# delete files? preprocssing only
delete_files = False
# make a refined stream fc
refine_streams = True
# Burn Streams?
burn = True
burn_stream_fc = hydro_dir + r"\BurnPath"
burn_buffer = 1
burn_smooth = 10
burn_drop = 100

# Square km catchment size where streams initiate
# Assumes stream initiation at of 0.04 square km via Clarke et al 2008
# Aproximates 70% probability of being perennial
# Modeling Streams and Hydrogeomorphic attributes in Oregon from digital and field data.
stream_init_sqkm = 0.04
stream_init_sqm = stream_init_sqkm * 1000000

# Meters from the stream that defines the RSA
rsa_m = 30

# Output Spatial reference. This should really
# be the same as the input DEM
# NAD_1983_HARN_Oregon_Statewide_Lambert_Feet_Intl
#sr = arcpy.SpatialReference(2994)
sr = arcpy.SpatialReference(6557)

env.workspace = hydro_dir
OUT_BE = env.workspace + "\\be"
OUT_BE_AGG = env.workspace + "\\be_agg"

OUT_SINKS = env.workspace + "\\sinks"
OUT_SINK_DRAINAGE = env.workspace + "\\sink_drainage"

OUT_BE_FILL = env.workspace + "\\be_fill"

OUT_BE_BURN = env.workspace + "\\be_burn"
OUT_BE_HYDRO_HS = env.workspace + "\\be_fill_hs"

OUT_FDR  = env.workspace + "\\fdr"
OUT_FAC = env.workspace + "\\fac"

NULL_MASK = env.workspace + "\\null_mask"
OUT_STREAMS_REFINE = env.workspace + "\\stream_refine"
OUT_STREAMS_REFINE2 = env.workspace + "\\stream_refine_backup"

OUT_STREAM1 = env.workspace + "\\stream1"
OUT_STREAM2 = env.workspace + "\\stream2"
OUT_STREAM_SEG1 =  env.workspace + "\\stream_seg"
OUT_STREAM_POLY = env.workspace + "\\stream_poly"
OUT_CATCHMENT = env.workspace + "\\catchment"
OUT_CATCHMENT_POLY  = env.workspace + "\\catchment_poly"

OUT_OUTLET_POINTS = env.workspace + "\\outlet_points"
OUT_OUTLET_RASTER1 = env.workspace + "\\outlets1"
OUT_OUTLET_RASTER2 = env.workspace + "\\outlets2"
OUT_UP_AREA  = env.workspace + "\\up_area"
OUT_FDR_STREAM = env.workspace + "\\fdr_stream"

OUT_FDR_OUTLET = env.workspace + "\\fdr_outlet"
OUT_TO_STREAM1 = env.workspace + "\\to_stream_nd"
OUT_TO_STREAM2 = env.workspace + "\\to_stream"

OUT_TO_STREAM_EUC = env.workspace + "\\to_stream_euc"
OUT_FDR_EUC3 = env.workspace + "\\fdr_euc"
OUT_FDR_EUC_OUTLET  = env.workspace + "\\fdr_euc_outlet"

OUT_FDR_EUCQ = env.workspace + "\\fdr_eucq"
OUT_FDR_EUCQ_OUTLET  = env.workspace + "\\fdr_eucq_outlet"

OUT_RSA_EUC_ZONE = env.workspace + "\\rsa_euc_zone"
OUT_RSA_Q_ZONE = env.workspace + "\\rsa_q_zone"
OUT_RSA_EUCQ_ZONE = env.workspace + "\\rsa_eucq_zone"

OUT_RSA_Q_WEIGHT = env.workspace + "\\rsa_q_weight"
OUT_RSA_EUC_WEIGHT = env.workspace + "\\rsa_euc_weight"
OUT_RSA_EUCQ_WEIGHT = env.workspace + "\\rsa_eucq_weight"

OUT_TO_OUTLET1 = env.workspace + "\\to_outlet_nd"
OUT_TO_OUTLET2 = env.workspace + "\\to_outlet"

OUT_FAC_RCA =  env.workspace + "\\fac_rca"
OUT_FAC_ARCA = env.workspace + "\\fac_arca"

OUT_FAC_RSA_EUC=  env.workspace + "\\fac_rsa_euc"
OUT_FAC_RSA_Q=  env.workspace + "\\fac_rsa_q"
OUT_FAC_RSA_EUCQ=  env.workspace + "\\fac_rsa_eucq"

OUT_FAC_ARSA_EUC =  env.workspace + "\\fac_arsa_euc"
OUT_FAC_ARSA_Q =  env.workspace + "\\fac_arsa_q"
OUT_FAC_ARSA_EUCQ =  env.workspace + "\\fac_arsa_eucq"

temp1 = env.workspace + "\\APUNIQUEID"
temp2 = env.workspace + "\\LAYERKEYTABLE"
temp3 = env.workspace + "\\stream_poly_FS"

# Reset geoprocessing environment settings
arcpy.ResetEnvironments()

delete_items = [OUT_BE_BURN,
                OUT_BE_FILL,
                OUT_FDR, OUT_FAC,
                OUT_STREAM_SEG1, 
                OUT_STREAM1, OUT_STREAM2,
                OUT_STREAM_POLY,
                OUT_STREAMS_REFINE, 
                temp1,
                temp2,
                temp3]

if delete_files:
    print("deleting files")
    for item in delete_items:
        arcpy.Delete_management(in_data=item)

# keeping track of time
startTime= time.time()
beginTime = startTime

def refineStreams():
    """Creates a feature class (and backup of existing ones) to
    review and refine which segments are streams."""

    if not arcpy.Exists(OUT_STREAMS_REFINE):
        print("refined stream poly")
        arcpy.CopyFeatures_management(OUT_STREAM_POLY, OUT_STREAMS_REFINE)
        
        arcpy.AddField_management(in_table=OUT_STREAMS_REFINE,
                                  field_name="isStream",
                                  field_type="SHORT")
    
    # Make Feature Layers for selection process
    arcpy.MakeFeatureLayer_management(in_features=OUT_STREAMS_REFINE,
                                         out_layer="stream_lyr")
        
    if arcpy.Exists(OUT_STREAMS_REFINE2):
        arcpy.MakeFeatureLayer_management(in_features=OUT_STREAMS_REFINE2,
                                          out_layer="refine_backup_lyr",
                                          where_clause="""isStream = 0""")    
    
        # Identify non streams from the previous backup  
        arcpy.SelectLayerByLocation_management(in_layer="stream_lyr",
                                               overlap_type="HAVE_THEIR_CENTER_IN",
                                               select_features="refine_backup_lyr")
    
        arcpy.CalculateField_management(in_table="stream_lyr", field="isStream",
                                        expression=0)
    
        arcpy.SelectLayerByAttribute_management(in_layer_or_view="stream_lyr",
                                                selection_type="CLEAR_SELECTION")    
    
    # Identify streams outside of predefined NULL areas
    
    if arcpy.Exists(NULL_MASK):
        arcpy.MakeFeatureLayer_management(in_features=NULL_MASK,
                                          out_layer="null_mask_lyr",
                                          where_clause="""isNULL = 1""")
        
        arcpy.SelectLayerByLocation_management(in_layer="stream_lyr",
                                               overlap_type="INTERSECT",
                                               select_features="null_mask_lyr",
                                               invert_spatial_relationship="INVERT")
        
        arcpy.SelectLayerByAttribute_management(in_layer_or_view="stream_lyr", 
                                               selection_type="REMOVE_FROM_SELECTION",
                                               where_clause="""isStream = 0""")    
        
        arcpy.CalculateField_management(in_table="stream_lyr", field="isStream",
                                        expression=1)
    
    # remove stubs shorter than riparian 
    # width of 150 ft (fc units are feet)
    arcpy.SelectLayerByAttribute_management(in_layer_or_view="stream_lyr", 
                                           selection_type="NEW_SELECTION",
                                           where_clause="""Strahler = 1 AND Shape_Length <= 150""")
    
    arcpy.CalculateField_management(in_table="stream_lyr",
                                    field="isStream",
                                    expression=0) 
    
    arcpy.SelectLayerByAttribute_management(in_layer_or_view="stream_lyr",
                                            selection_type="CLEAR_SELECTION")
        
    delete_items = [OUT_STREAM_SEG1, 
                    OUT_STREAM1, OUT_STREAM2,
                    OUT_STREAM_POLY,
                    OUT_STREAMS_REFINE2,
                    temp1,
                    temp2,
                    temp3]
    
    print("deleting stream raster files")
    for item in delete_items:
        arcpy.Delete_management(in_data=item)
    
    # Make a new backup from an existing one
    arcpy.CopyFeatures_management(OUT_STREAMS_REFINE, OUT_STREAMS_REFINE2)      
    
    arcpy.MakeFeatureLayer_management(in_features=OUT_STREAMS_REFINE,
                                      out_layer="stream_refine_1",
                                      where_clause="""isStream = 1""")

    print("Stream Definition using refined streams")
    arcpy.PolylineToRaster_conversion(in_features="stream_refine_1",
                                      value_field="isStream",
                                      out_rasterdataset=OUT_STREAM1)    
    


#-- 1a. Aggregate -------------------------
# this is only needed if downscaling from 3ft
if not arcpy.Exists(OUT_BE_AGG) and agg:
    print("elevation aggregate")
    BE_AGG = Aggregate(in_raster=OUT_BE, cell_factor=agg_factor,
                       aggregation_type="MEAN")
    BE_AGG.save(OUT_BE_AGG)
    
    BE = Raster(OUT_BE_AGG)
    con_to_m = arcpy.Describe(BE).SpatialReference.metersPerUnit
    con_from_m = 1 / con_to_m
    cell_size = arcpy.Describe(BE).meanCellWidth
    init_cells_sqkm = int(stream_init_sqkm / ((cell_size * con_to_m / 1000) ** 2))
    
    print("{0:.1f} minutes".format((time.time() - beginTime) / 60))
    beginTime = time.time()    
    
    # Set env settings
    env.overwriteOutput = True
    env.cellSize = cell_size
    env.snapRaster = OUT_BE_AGG
    env.extent = OUT_BE_AGG
    env.mask = OUT_BE_AGG
    env.outputCoordinateSystem = sr
    
elif agg:
    BE = Raster(OUT_BE_AGG)
    
    con_to_m = arcpy.Describe(BE).SpatialReference.metersPerUnit
    con_from_m = 1 / con_to_m
    cell_size = arcpy.Describe(BE).meanCellWidth
    init_cells_sqkm = int(stream_init_sqkm / ((cell_size * con_to_m / 1000) ** 2))
    
    # Set env settings
    env.overwriteOutput = True
    env.cellSize = cell_size
    env.snapRaster = OUT_BE_AGG
    env.extent = OUT_BE_AGG
    env.mask = OUT_BE_AGG
    env.outputCoordinateSystem = sr
    
else:
    BE = Raster(OUT_BE)

    con_to_m = arcpy.Describe(BE).SpatialReference.metersPerUnit
    con_from_m = 1 / con_to_m
    cell_size = arcpy.Describe(BE).meanCellWidth
    cell_size = 9.0
    init_cells_sqkm = int(stream_init_sqkm / ((cell_size * con_to_m / 1000) ** 2))
    
    # Set env settings
    env.overwriteOutput = True
    env.cellSize = cell_size
    env.snapRaster = OUT_BE
    env.extent = OUT_BE
    env.mask = OUT_BE_AGG
    env.outputCoordinateSystem = sr
 
#-- 1b. Sinks -------------------------
if make_sinks and not arcpy.Exists(OUT_SINKS):
    print("Sinks")
    
    ArcHydroTools.SinkEvaluation(Input_DEM_Raster=BE,
                                 Output_Sink_Polygon_Feature_Class=OUT_SINKS,
                                 Output_Sink_Drainage_Area_Feature_Class=OUT_SINK_DRAINAGE)
    
    print("{0:.1f} minutes".format((time.time() - beginTime) / 60))
    beginTime = time.time()    
    
if refine_streams:
    refineStreams()
            
if burn: 
    #-- Burn existing stream features into the DEM
    if not arcpy.Exists(OUT_BE_BURN):
        print("burn stream features")
        ArcHydroTools.DEMReconditioning(Input_Raw_DEM_Raster=BE, 
                                       Input_Stream_Raster_or_Feature_Class=burn_stream_fc, 
                                       Number_of_Cells_for_Stream_Buffer=burn_buffer, 
                                       Smooth_Drop_in_Z_Units=burn_drop, 
                                       Sharp_Drop_in_Z_Units=burn_drop, 
                                       Output_AGREE_DEM_Raster=OUT_BE_BURN)
    
    BE = Raster(OUT_BE_BURN)
    
    print("{0:.1f} minutes".format((time.time() - beginTime) / 60))
    beginTime = time.time()
        
#-- 2. Fill -------------------------
if not arcpy.Exists(OUT_BE_FILL):
    print("fill")
    
    ArcHydroTools.FillSinks(Input_DEM_Raster=BE,
                                   Output_Hydro_DEM_Raster=OUT_BE_FILL)
    
BE_HYDRO = Raster(OUT_BE_FILL)

#if not arcpy.Exists(OUT_BE_HYDRO_HS):
#    print("hydro hillshade")
#    BE_HYDRO_HS = Hillshade(BE_HYDRO, 315, 45, "NO_SHADOWS", 1)
#    BE_HYDRO_HS.save(OUT_BE_HYDRO_HS)
    
print("{0:.1f} minutes".format((time.time() - beginTime) / 60))
beginTime = time.time()

# ----------------------------------------------------------------------
# Generate Base Hydro outputs
# ----------------------------------------------------------------------

#-- 3. Flow Direction -------------------------    
if not arcpy.Exists(OUT_FDR):
    print("flow direction")
    
    ArcHydroTools.FlowDirection(BE_HYDRO, OUT_FDR)
    
    print("{0:.1f} minutes".format((time.time() - beginTime) / 60))
    beginTime = time.time()         
    
FDR = Raster(OUT_FDR)

# -- 4. Flow Accumulation  -------------------------
if not arcpy.Exists(OUT_FAC):
    print("flow accumulation")
    ArcHydroTools.FlowAccumulation(FDR, OUT_FAC)
    
    print("{0:.1f} minutes".format((time.time() - beginTime) / 60))
    beginTime = time.time()     
        
FAC = Raster(OUT_FAC)

# stats need to be recalculated if the FAC is large
arcpy.CalculateStatistics_management(in_raster_dataset=FAC,skip_existing="OVERWRITE")

# -- 5. Stream Raster with NoData  -------------------------
if not arcpy.Exists(OUT_STREAM1):
    print("Stream Definition")
    ArcHydroTools.StreamDefinition(Input_Flow_Accumulation_Raster=FAC,
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
    ArcHydroTools.StreamSegmentation(Input_Stream_Raster=STREAM1, 
                                    Input_Flow_Direction_Raster=FDR, 
                                    Output_Stream_Link_Raster=OUT_STREAM_SEG1)
    STREAM_SEGS = Raster(OUT_STREAM_SEG1)
    
else:
    STREAM_SEGS = Raster(OUT_STREAM_SEG1)

# -- 8. Stream Poly -------------------------
if not arcpy.Exists(OUT_STREAM_POLY):
    print("Stream Poly")
    ArcHydroTools.DrainageLineProcessing(Input_Stream_Link_Raster=STREAM_SEGS,
                                         Input_Flow_Direction_Raster=FDR,
                                         Output_Drainage_Line_Feature_Class=OUT_STREAM_POLY)
    
    # Add Strahler stream order
    print("Adding strahler stream order")
    arcpy.AddField_management(in_table=OUT_STREAM_POLY,
                              field_name="Strahler", field_type="SHORT")    
    
    ArcHydroTools.AssignRiverOrder(Input_Feature_Class_or_Table=OUT_STREAM_POLY, 
                                  Input_River_Order_Field="Strahler", 
                                  River_Order_Type="Strahler")

    print("{0:.1f} minutes".format((time.time() - beginTime) / 60))
    beginTime = time.time()
    
print("Total process: {0:.1f} minutes".format((time.time() - startTime) / 60))
 
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
    ArcHydroTools.DrainagePointProcessing(FAC, 
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
    UP_AREA = FAC * ((cell_size * con_to_m)**2)
    UP_AREA.save(OUT_UP_AREA)
else:
    UP_AREA = Raster(OUT_UP_AREA)
    
# -- 15. Flow Direction w/ NULL streams  -------------------------
if not arcpy.Exists(OUT_FDR_STREAM):
    print("flow direction w/ null streams")
    
    # square meters
    stream_init_sqm = stream_init_sqkm * 1000000              
                
    FDR_STREAM = SetNull(in_conditional_raster=((UP_AREA >= stream_init_sqm) | (STREAM2==1)),
                         in_false_raster_or_constant=FDR)          

    FDR_STREAM.save(OUT_FDR_STREAM)
else:
    FDR_STREAM = Raster(OUT_FDR_STREAM)
    
# -- 16. Flow Direction w/ NULL Outlets  -------------------------
if not arcpy.Exists(OUT_FDR_OUTLET):
    print("flow direction w/ null outlets")
    
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
      
# ----------------------------------------------------------------------
# Generate Base RCA and ARCA Flow Accumulation outputs
# ----------------------------------------------------------------------

# -- 19. Generate RCA FAC raster -------------------------
if not arcpy.Exists(OUT_FAC_RCA):
    print("RCA fac raster")
    
    FAC_RCA = Plus(FlowAccumulation(in_flow_direction_raster=FDR_OUTLET, 
                               data_type="FLOAT"), 1.0)

    FAC_RCA.save(OUT_FAC_RCA)
    
# -- 20. Generate ARCA FAC raster -------------------------
if not arcpy.Exists(OUT_FAC_ARCA):
    print("ARCA fac raster")
    FAC_ARCA = Plus(FAC, 1.0)
    FAC_ARCA.save(OUT_FAC_ARCA)
    

# ----------------------------------------------------------------------
# RSA and ARSA outputs based based on euclidean distance
# ----------------------------------------------------------------------

# -- 21. Generate a rsa zone raster based on euclidean distance --------
if not arcpy.Exists(OUT_RSA_EUC_ZONE):
    print("Euclidean RSA allocation zones")
    RSA_EUC_ZONES = EucAllocation(in_source_data=STREAM_SEGS,
                              maximum_distance=rsa_m*con_from_m,
                              source_field="Value")
    RSA_EUC_ZONES.save(OUT_RSA_EUC_ZONE)
else:
    RSA_EUC_ZONES = Raster(OUT_RSA_EUC_ZONE)
    
# -- 22. Generate an euclidean distance raster -------------------------
if not arcpy.Exists(OUT_TO_STREAM_EUC):
    print("Euclidean flow direction raster")
    TO_STREAM_EUC = EucDistance(STREAM1, maximum_distance=rsa_m*con_from_m) * con_to_m
    TO_STREAM_EUC.save(OUT_TO_STREAM_EUC)
else:
    TO_STREAM_EUC = Raster(OUT_TO_STREAM_EUC)

# -- 23. Generate an euclidean distance flow direction raster -----------
if not arcpy.Exists(OUT_FDR_EUC3):
    print("Euclidean flow direction raster")
    FDR_EUC1 = EucDirection(STREAM1, maximum_distance=rsa_m*con_from_m)
     
    rc_table = RemapRange([[1, 22.5, 64],
                           [22.5,67.5, 128],
                           [67.5, 112.5, 1],
                           [112.5, 157.5, 2],
                           [157.5, 202.5, 4],
                           [202.5, 247.5, 8],
                           [247.5, 292.5, 16],
                           [292.5, 337.5, 32],
                           [337.5, 360, 64]
                           ])
    
    # reclass
    FDR_EUC2 = Reclassify(in_raster=FDR_EUC1,
                            reclass_field="value",
                            remap=rc_table,
                            missing_values="DATA")
    
    # zero is the stream
    FDR_EUC3 = Con(in_conditional_raster=(FDR_EUC2==0),
                         in_true_raster_or_constant=FDR,
                         in_false_raster_or_constant=FDR_EUC2)     
    
    FDR_EUC3.save(OUT_FDR_EUC3)
else:
    FDR_EUC3 = Raster(OUT_FDR_EUC3)
    

# -- 24. Generate an euclidean distance flow direction w/ null outlets 
if not arcpy.Exists(OUT_FDR_EUC_OUTLET):
    print("euclidean flow direction w/ null outlets")
    
    FDR_EUC_OUTLET = SetNull(in_conditional_raster=(OUTLETS2==1),
                         in_false_raster_or_constant=FDR_EUC3)

    FDR_EUC_OUTLET.save(OUT_FDR_EUC_OUTLET)
else:
    FDR_EUC_OUTLET = Raster(OUT_FDR_EUC_OUTLET)
    
# -- 25. Generate RSA euclidean distance weight raster -----------------
if not arcpy.Exists(OUT_RSA_EUC_WEIGHT):
    print("RSA weight raster")
    
    RSA_EUC_WEIGHT = SetNull(in_conditional_raster=(TO_STREAM_EUC > rsa_m),
                         in_false_raster_or_constant=1)

    RSA_EUC_WEIGHT.save(OUT_RSA_EUC_WEIGHT)
else:
    RSA_EUC_WEIGHT = Raster(OUT_RSA_EUC_WEIGHT)

# -- 26. Generate Euclidean distance RSA FAC raster ---------------------
if not arcpy.Exists(OUT_FAC_RSA_EUCQ):
    print("RSA Euclidean distance fac raster")
    
    FAC_RSA_EUC = Plus(FlowAccumulation(in_flow_direction_raster=Times(FDR_EUC_OUTLET, RSA_EUC_WEIGHT),
                                 in_weight_raster=RSA_EUC_WEIGHT, 
                                 data_type="FLOAT"), 1.0)

    FAC_RSA_EUC.save(OUT_FAC_RSA_EUC)

# -- 27. Generate euclidean distance ARSA FAC raster --------------------
if not arcpy.Exists(OUT_FAC_ARSA_EUCQ):
    print("ARSA Euclidean distance fac raster")
    
    FAC_ARSA_EUC = Plus(FlowAccumulation(in_flow_direction_raster=Times(FDR_EUC3, RSA_EUC_WEIGHT),
                                 in_weight_raster=RSA_EUC_WEIGHT, 
                                 data_type="FLOAT"), 1.0)

    FAC_ARSA_EUC.save(OUT_FAC_ARSA_EUC)

# ----------------------------------------------------------------------
# RSA and ARSA outputs based on Flow distance
# ----------------------------------------------------------------------
    
# -- 28. Generate RSA flow weight raster -------------------------
if not arcpy.Exists(OUT_RSA_Q_WEIGHT):
    print("RSA flow distance weight raster")
    
    RSA_Q_WEIGHT = SetNull(in_conditional_raster=(TO_STREAM2 > rsa_m),
                         in_false_raster_or_constant=1)

    RSA_Q_WEIGHT.save(OUT_RSA_Q_WEIGHT)
else:
    RSA_Q_WEIGHT = Raster(OUT_RSA_Q_WEIGHT)

# -- 29. Generate RSA flow distance zone raster -------------------------
if not arcpy.Exists(OUT_RSA_Q_ZONE):
    print("RSA flow distance zone raster")
    
    RSA_Q_ZONE = Con(in_conditional_raster=(RSA_Q_WEIGHT==1),
                         in_true_raster_or_constant=CATCHMENT)
    
    RSA_Q_ZONE.save(OUT_RSA_Q_ZONE)
    

# -- 30. Generate flow distance RSA FAC raster -------------------------
if not arcpy.Exists(OUT_FAC_RSA_Q):
    print("RSA flow distance fac raster")
    
    FAC_RSA_EUCQ = Plus(FlowAccumulation(in_flow_direction_raster=Times(FDR_OUTLET, RSA_Q_WEIGHT),
                                 in_weight_raster=RSA_Q_WEIGHT, 
                                 data_type="FLOAT"), 1.0)

    FAC_RSA_EUCQ.save(OUT_FAC_RSA_Q)

# -- 31. Generate flow distance ARSA FAC raster -------------------------
if not arcpy.Exists(OUT_FAC_ARSA_Q):
    print("ARSA flow distance fac raster")
    
    FAC_ARSA_Q = Plus(FlowAccumulation(in_flow_direction_raster=Times(FDR, RSA_Q_WEIGHT),
                                 in_weight_raster=RSA_Q_WEIGHT, 
                                 data_type="FLOAT"), 1.0)

    FAC_ARSA_Q.save(OUT_FAC_ARSA_Q)
    
# ----------------------------------------------------------------------
# RSA and ARSA  outputs based on combination of Euclidean and Flow distance
# ----------------------------------------------------------------------

# -- 32. Reconcile RSA zones and catchments ---------------------------
if not arcpy.Exists(OUT_RSA_EUCQ_ZONE):
    print("Reconcile RSA euclidean zones and catchments")
        
    RSA_EUCQ_ZONE = Con(in_conditional_raster=Divide(Plus(Times(CATCHMENT, 10),
                                                          Times(RSA_EUC_ZONES, 10)), 2) == Times(RSA_EUC_ZONES, 10),
                        in_true_raster_or_constant=RSA_EUC_ZONES,
                        in_false_raster_or_constant=SetNull(in_conditional_raster=(TO_STREAM2 > rsa_m),
                            in_false_raster_or_constant=CATCHMENT))
    RSA_EUCQ_ZONE.save(OUT_RSA_EUCQ_ZONE)


# -- 33. Generate a FDR based on the euclidean flow reconciliation ----
if not arcpy.Exists(OUT_FDR_EUCQ):
    print("FDR for the euclidean-flow reconciliation ")
        
    FDR_EUCQ = Con(in_conditional_raster=Divide(Plus(Times(CATCHMENT, 10),
                                                          Times(RSA_EUC_ZONES, 10)), 2) == Times(RSA_EUC_ZONES, 10),
                        in_true_raster_or_constant=FDR_EUC3,
                        in_false_raster_or_constant=SetNull(in_conditional_raster=(TO_STREAM2 > rsa_m),
                            in_false_raster_or_constant=FDR))
    FDR_EUCQ.save(OUT_FDR_EUCQ)


# -- 34. Generate an euclidean distance flow reconciled flow direction w/ null outlets 
if not arcpy.Exists(OUT_FDR_EUCQ_OUTLET):
    print("euclidean-flow reconciled flow direction w/ null outlets")
    
    FDR_EUCQ_OUTLET = SetNull(in_conditional_raster=(OUTLETS2==1),
                         in_false_raster_or_constant=FDR_EUCQ)

    FDR_EUCQ_OUTLET.save(OUT_FDR_EUCQ_OUTLET)
else:
    FDR_EUCQ_OUTLET = Raster(OUT_FDR_EUCQ_OUTLET)
    
# -- 35. Generate an euclidean distance flow reconciled weight raster --
if not arcpy.Exists(OUT_RSA_EUCQ_WEIGHT):
    print("RSA euclidean-flow reconciled weight raster")
    
    RSA_EUCQ_WEIGHT = Con(in_conditional_raster=Divide(Plus(Times(CATCHMENT, 10),
                                                            Times(RSA_EUC_ZONES, 10)), 2) == Times(RSA_EUC_ZONES, 10),
                          in_true_raster_or_constant=1,
                          in_false_raster_or_constant=SetNull(in_conditional_raster=(TO_STREAM2 > rsa_m),
                              in_false_raster_or_constant=1))

    RSA_EUCQ_WEIGHT.save(OUT_RSA_EUCQ_WEIGHT)
else:
    RSA_EUCQ_WEIGHT = Raster(OUT_RSA_EUCQ_WEIGHT)
    
     
# -- 36. Generate Euclidean-flow reconciled RSA FAC raster --------------
if not arcpy.Exists(OUT_FAC_RSA_EUCQ):
    print("RSA euclidean-flow reconciled fac raster")
    
    FAC_RSA_EUCQ = Plus(FlowAccumulation(in_flow_direction_raster=Times(FDR_EUCQ_OUTLET, RSA_EUCQ_WEIGHT),
                                 in_weight_raster=RSA_EUCQ_WEIGHT, 
                                 data_type="FLOAT"), 1.0)

    FAC_RSA_EUCQ.save(OUT_FAC_RSA_EUCQ)

# -- 37. Generate Euclidean-flow reconciled ARSA FAC raster ------------
if not arcpy.Exists(OUT_FAC_ARSA_EUCQ):
    print("ARSA euclidean-flow reconciled fac raster")
    
    FAC_ARSA_EUCQ = Plus(FlowAccumulation(in_flow_direction_raster=Times(FDR_EUCQ, RSA_EUCQ_WEIGHT),
                                 in_weight_raster=RSA_EUCQ_WEIGHT, 
                                 data_type="FLOAT"), 1.0)

    FAC_ARSA_EUCQ.save(OUT_FAC_ARSA_EUCQ)


print("Total process: {0:.1f} minutes".format((time.time() - StartTime) / 60))
print("done")