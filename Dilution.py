
from __future__ import division, print_function
from collections import defaultdict
from math import ceil, atan2, degrees
from operator import itemgetter
import sys
import os
import numpy
import arcpy
import ArcHydroTools
from arcpy import env
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")

# Paramters
node_dx = 100  # meters
buffer_widths = [30, 50, 70, 90, 110]  #feet
checkDirection = False

# This is the # of cells needed for stream initiation via Clarke et al 2008 - 
# Modeling Streams and Hydrogeomorphic attributes in Oregon from digital and field data.
# (0.360 square km) = 400 x 30 x 30m cells
stream_init = 400  #(3600 if using 10 meter DEM)
stream_init_km = 0.360

# Inputs
target_gdb = r"C:\WorkSpace\ODF_Riparian_Rulemaking\GIS\Umpqua.gdb"
in_dem = target_gdb + r"\in_DEM_10m"
in_stream_fc = target_gdb + r"\in_NHDHv21_flowline_ogic"
in_ssbt_raster = target_gdb + r"\in_SSBT_ODF"  # this is a raster where 1 = SSBT
# this is a raster where 1 = typeF stream using SSBT from ODF + 
# Rainbow_HEM_FC + CoastalCUtt_HEM_FC, and Western BrkLamp_HEM_FC from ODFW FHD_Resident_Pub20141117.gdb
in_typef_raster = target_gdb + r"\in_TYPEF_ODFW"  

# Temp Outputs
out_dem_burn = target_gdb + r"\s01_dem_burn"
out_dem_burnsinks = target_gdb + r"\s02_dem_burn_sinks"
out_fdr = target_gdb + r"\s03_fdr"
out_fac = target_gdb + r"\s04_fac"
out_str_raster = target_gdb + r"\s05_str"
out_strlink_raster = target_gdb + r"\s06_strlink"
out_fac_stats = target_gdb + r"\s07_fac_min_max"

out_strlink_fc = target_gdb + r"\s08_stream_fc"

out_ssbt_focal = target_gdb + r"\s09_ssbt_focal_sum"
out_ssbt_product = target_gdb + r"\s10_ssbt_product"
out_ssbt_strlink = target_gdb + r"\s11_ssbt_strlink" 
out_ssbt_fc = target_gdb + r"\s12_ssbt_fc"
out_upstream_fc = target_gdb + r"\s13_upstream"

out_typef_focal = target_gdb + r"\s14_typef_focal_sum"
out_typef_product = target_gdb + r"\s15_typef_product"
out_typef_strlink = target_gdb + r"\s16_typef_strlink" 
out_typef_fc = target_gdb + r"\s17_typef_fc"

out_typen_upstream_fc = target_gdb + r"\s18_typen_fc"
out_typef_non_ssbt = target_gdb + r"\s19_typef_nonssbt_fc"
out_upstream_merge = target_gdb + r"\s20_upstream_merge_fc"
out_upstream_final_fc = target_gdb + r"\s21_upstream_final_fc"
out_split_nodes_fc = target_gdb + r"\s22_upstream_split_nodes"
out_attr_nodes_fc = target_gdb + r"\s23_upstream_attribute_nodes"

out_upstream_split_fc = target_gdb + r"\s24_upstream_reaches"
out_upstream_attr_fc = target_gdb + r"\s25_upstream_attr_reaches"

arcpy.env.overwriteOutput = True
arcpy.env.snapRaster = out_fdr

def nested_dict(): 
    """Build a nested dictionary"""
    return defaultdict(nested_dict)

def to_meters_con(inFeature):
    """Returns the conversion factor to get from the
    input spatial units to meters"""
    try:
        con_to_m = arcpy.Describe(inFeature).SpatialReference.metersPerUnit
    except:
        arcpy.AddError("{0} has a coordinate system ".format(inFeature)+
                       "that is not projected or not recognized. "+
                       "Use a projected coordinate system "
                       "preferably in linear units of feet or meters.")
        sys.exit("Coordinate system is not projected or not recognized. "+
                 "Use a projected coordinate system, preferably in linear "+
                 "units of feet or meters.")
    return con_to_m
    
def from_meters_con(inFeature):
    """Returns the conversion factor to get from meters to the
    spatial units of the input feature class"""
    try:
        con_from_m = 1 / arcpy.Describe(inFeature).SpatialReference.metersPerUnit
    except:
        arcpy.AddError("{0} has a coordinate system ".format(inFeature)+
                       "that is not projected or not recognized. "+
                       "Use a projected coordinate system "
                       "preferably in linear units of feet or meters.")
        sys.exit("Coordinate system is not projected or not recognized. "+
                 "Use a projected coordinate system, preferably in linear "+
                 "units of feet or meters.")
    return con_from_m

def stream_walk(dict, key, key_list, junctions, hid_walk, gid_ssbt_list):
    """Walks downstream until the outlet is reached and returns the
    total length in meters"""
    
    next_down = dict[key]["NextDownID"]
    gid = dict[key]["GridID"]
    if next_down in key_list:
        length = dict[next_down]["length_m"]
        outlet = False
        junctions = junctions + 1
        hid_walk.append(next_down)
    else:
        if gid not in gid_ssbt_list:
            junctions = junctions + 1
        next_down = -1
        length = 0
        outlet = True
    return next_down, length, outlet, junctions, hid_walk

def create_node_list(streamline_fc, streamline_fc_ds, checkDirection, z_raster, node_dx):
    """Reads an input stream centerline file and returns the NODE ID,
    HYDRO ID, and X/Y coordinates as a list"""
    nodeList = []
    attrList = []
    incursorFields = ["SHAPE@","SHAPE@LENGTH", "HydroID", "GridID", "NextDownID", "DF", "DS_MIX", "TRIB"]
    nodeID = 1
    # Determine input projection and spatial units
    proj = arcpy.Describe(streamline_fc).spatialReference
    con_from_m = from_meters_con(streamline_fc)
    con_to_m = to_meters_con(streamline_fc)
    
    # convert the node dx to units of the input feature class
    node_dx_fc = node_dx * con_from_m
    
    # create a dictionary with the hydro ids as the key and 
        # population with the next down id and feature length in meters    
    usDict = nested_dict()
    gid_list = []
    hid_list = []
    with arcpy.da.SearchCursor(streamline_fc, ["HydroID", "NextDownID", "GridID", "SHAPE@LENGTH"]) as Inrows:
        for row in Inrows:
            usDict[row[0]]["NextDownID"] = row[1]
            usDict[row[0]]["GridID"] = row[2]
            usDict[row[0]]["length_m"] = row[3] * con_to_m
            
            # Pull the upstream hydro and grid IDs into a list
            hid_list.append(row[0])
            gid_list.append(row[2])

    #Pull the ssbt grid IDs into a list
    gid_ssbt_list = []
    with arcpy.da.SearchCursor(streamline_fc_ds, ["GridID"]) as Inrows:
        for row in Inrows:
            gid_ssbt_list.append(row[0])
    
    # Check for duplicate hids
    dups = list(set([i for i in hid_list if hid_list.count(i) > 1]))
    if dups:
        sys.exit("There are duplicate hydro IDs in your input stream"+
                 "feature class."+
                 "\nHere are the duplicates:  \n"+
                 "{0}".format(dups))        
    
    # Now create the nodes. I'm pulling the fc data twice because on 
    # speed tests it is faster compared to saving all the incursorFields 
    # to a list and iterating over the list        
    print("Creating Nodes")
    with arcpy.da.SearchCursor(streamline_fc, incursorFields,"",proj) as Inrows:
        for row in Inrows:    
            lineLength = row[1] # These units are in the units of projection
            this_hid = row[2]
            this_gid = row[3]
            next_down = this_hid
            meters_to_ssbt = 0
            hid_walk = [this_hid]
            junctions = 0
            while True:
                next_down, length, outlet, junctions, hid_walk = stream_walk(
                    usDict, next_down, hid_list, junctions, hid_walk, gid_ssbt_list)
                meters_to_ssbt = meters_to_ssbt + length
                if outlet is True:
                    for h in range(0, len(hid_walk)):
                        usDict[hid_walk[h]]["Junctions"] = junctions-h
                    break             
            this_junction = usDict[this_hid]["Junctions"]
            
            # This is the remainder distance between the last split node 
            # and the top of the downstream reach.
            # This distance is used to adjust the first node on 
            # this stream so it is equal to dx.
            # Distance is in units of the feature class             
            adj = meters_to_ssbt % node_dx * con_from_m 
            
            numNodes = int(((lineLength + adj) * con_to_m)/ node_dx)
            nodes = range(1,numNodes+1)
            mid = range(0,numNodes)
            
            if checkDirection is True:
                flip = check_stream_direction(row[0], z_raster, row[2])
            else:
                flip = 1

            # list of percentage of feature length to traverse
            positions = [((n * node_dx * con_from_m) - adj) / lineLength for n in nodes]
            positions2 = [((n * node_dx * con_from_m) - adj - (node_dx_fc/ 2)) / lineLength for n in nodes]
            
            # remove 1st element cause it's just wrong and get first element
            if positions:
                del positions2[0]
                last = positions[-1]
            else:
                last = 0
            
            # add a node for the beginning and end
            positions.append(1)
            positions2.append(1-((1-last)/2))
            positions2.insert(0, (node_dx_fc - adj)/2/lineLength) 
            
            mid_distance = node_dx * con_from_m / lineLength
            
            for i in range(0, len(positions)):
            #for position in positions:
                node = row[0].positionAlongLine(abs(flip - positions[i]),
                                                True).centroid
                node2 = row[0].positionAlongLine(abs(flip - positions2[i]),
                                                True).centroid                
                
                node_meters_to_ssbt = float(meters_to_ssbt +
                                            (positions[i] * lineLength * con_to_m))
                # Get the coordinates at the up/down midway point along
                # the line between nodes and calculate the stream azimuth
                if positions[i] == 0.0:
                    mid_up = row[0].positionAlongLine(
                        abs(flip - (positions[i] + mid_distance)),True).centroid
                    mid_down = node
                elif 0.0 < positions[i] + mid_distance < 1:
                    mid_up = row[0].positionAlongLine(
                        abs(flip - (positions[i] + mid_distance)),True).centroid
                    mid_down = row[0].positionAlongLine(
                        abs(flip - (positions[i] - mid_distance)),True).centroid
                else:
                    mid_up = node
                    mid_down = row[0].positionAlongLine(
                        abs(flip - (positions[i] - mid_distance)),True).centroid
            
                stream_azimuth = degrees(atan2((mid_down.X - mid_up.X),
                                               (mid_down.Y - mid_up.Y)))
                if stream_azimuth < 0:
                    stream_azimuth = stream_azimuth + 360
                    
                # list of "NODE_ID",HydroID,"GridID","NextDownID", "DF", 
                # "DS_MIX", "TRIB","M_FROM_SSBT", "JUNC_TO_SSBT",STREAM_AZMTH,
                # "POINT_X","POINT_Y","SHAPE@X","SHAPE@Y"
                nodeList.append((nodeID, row[2], row[3], row[4], row[5],
                                 row[6], row[7], node_meters_to_ssbt, 
                                 stream_azimuth,
                                 this_junction,
                                 node.X, node.Y,
                                 node.X, node.Y))
                
                attrList.append((node_meters_to_ssbt, 
                                 this_junction, stream_azimuth,
                                 node2.X, node2.Y,
                                 node2.X, node2.Y))                
                
                nodeID = nodeID + 1
    return(nodeList, attrList)

def create_nodes_fc(nodeList, nodes_fc, streamline_fc, cursorfields, proj):
    """Create the output point feature class using
    the data from the nodes list"""
    print("Exporting Data")
    
    #Create an empty output with the same projection as the input polyline   
    arcpy.CreateFeatureclass_management(os.path.dirname(nodes_fc),
                                        os.path.basename(nodes_fc),
                                        "POINT","","DISABLED","DISABLED",proj)

    # Add attribute fields
    f_list = [field.name for field in arcpy.ListFields(streamline_fc)]
   
    for f in cursorfields:
        if f in f_list:
            # Get field properties
            f_type = arcpy.ListFields(streamline_fc,f)[0].type
            f_precision = arcpy.ListFields(streamline_fc,f)[0].precision
            f_scale = arcpy.ListFields(streamline_fc,f)[0].scale
            f_length = arcpy.ListFields(streamline_fc,f)[0].length        
            
            arcpy.AddField_management(nodes_fc, f, f_type, f_precision,
                                          f_scale, f_length, "",
                                          "NULLABLE", "NON_REQUIRED")
        else:
            arcpy.AddField_management(nodes_fc, f, "DOUBLE", "", "", "",
                                      "", "NULLABLE", "NON_REQUIRED")            

    with arcpy.da.InsertCursor(nodes_fc, cursorfields + ["SHAPE@X","SHAPE@Y"]) as cursor:
        for row in nodeList:
            cursor.insertRow(row)

    #Change X/Y from input spatial units to decimal degrees
    proj_dd = arcpy.SpatialReference(4326) # GCS_WGS_1984
    with arcpy.da.UpdateCursor(nodes_fc,["SHAPE@X","SHAPE@Y","LONGITUDE",
                                         "LATITUDE"],"",proj_dd) as cursor:
        for row in cursor:
            row[2] = row[0] # LONGITUDE
            row[3] = row[1] # LATITUDE
            cursor.updateRow(row)

# to correct SSBT polyline vertices
# snap tool
# feature vertices to points Dangle


# Catchment grid
# Catchment polygon
# Drainage Point
# Hydro Network Generation



# DEM recondition (make sure flowline and dem are in same gdb)
if arcpy.Exists(out_dem_burn) is False:
    ArcHydroTools.DEMReconditioning(in_rawdem_raster=in_dem, 
                                   in_agreestream_features=in_stream_fc, 
                                   number_cells_buffer=1, 
                                   zdrop_smooth=10,
                                   zdrop_sharp=10000, 
                                   out_agreedem_raster=out_dem_burn, 
                                   raise_negative=None)
print("1. dem recondition done")

# Fill sinks
if arcpy.Exists(out_dem_burnsinks) is False:
    ArcHydroTools.FillSinks(in_dem_raster=out_dem_burn, out_hydrodem_raster=out_dem_burnsinks)
print("2. fill sinks done")

# flow direction
if arcpy.Exists(out_fdr) is False:
    ArcHydroTools.FlowDirection(in_hydrodem_raster=out_dem_burnsinks, 
                               out_flow_direction_raster=out_fdr)
print("3. fdr done")

# flow accumulation
if arcpy.Exists(out_fac) is False:
    ArcHydroTools.FlowAccumulation(in_flow_direction_raster=out_fdr, 
                                  out_flow_accumulation_raster=out_fac)
print("4. fac done")

# using minimum stream initiation size to identify cells that are streams.
# the other cells go to no data
if arcpy.Exists(out_str_raster) is False:
    ArcHydroTools.StreamDefinition(in_flowaccumulation_raster=out_fac,
                                   number_cells=stream_init, 
                                   out_stream_raster=out_str_raster, 
                                   area_sqkm=stream_init_km)
print("5. stream done")

# Create a raster with a unique id for each stream (sid/stream link)
if arcpy.Exists(out_strlink_raster) is False:
    ArcHydroTools.StreamSegmentation(in_stream_raster=out_str_raster, 
                                 in_flow_direction_raster=out_fdr, 
                                 out_streamlink_raster=out_strlink_raster, 
                                 in_sink_watershed_raster=None, 
                                 in_sink_link_raster=None)
print("6. stream sid done")

# Output a table of the strahler and min and max FAC value for each stream. 
# This is used to determine the incoming flow for each tributary
if arcpy.Exists(out_fac_stats) is False:
    ZonalStatisticsAsTable(out_strlink_raster,"VALUE", out_fac,
                           out_fac_stats,"DATA","MIN_MAX")
print("7. fac sid zonal stats done")

# Output polyline fc for each stream. The TO/FROM id is 
# used to look up fromthe min/max table the trib and 
# total mix values for dilution.
if arcpy.Exists(out_strlink_fc) is False:
    ArcHydroTools.DrainageLineProcessing(in_link_raster=out_strlink_raster, 
                                     in_flow_direction_raster=out_fdr, 
                                     out_drainageline_features=out_strlink_fc)
print("8a. stream polyline done")

# ---- Dilution factors -------------------------------------------------

# read stream fc into a dictionary using hydro id (hid) as key
hidDict = nested_dict()
with arcpy.da.SearchCursor(out_strlink_fc, ["HydroID","GridID", "NextDownID"]) as Inrows:
    for row in Inrows:
        hidDict[row[0]]["GridID"] = row[1] 
        hidDict[row[0]]["NextDownID"] = row[2]

# read tables into a dictionary using the stream GridID (gid) as key
gidDict = nested_dict() 
with arcpy.da.SearchCursor(out_fac_stats, ["Value","MIN", "MAX"]) as Inrows:
    for row in Inrows:
        gidDict[row[0]]["MIN"] = row[1] 
        gidDict[row[0]]["MAX"] = row[2]
        
# Get a list of existing fields
existingFields = []
for f in arcpy.ListFields(out_strlink_fc):
    existingFields.append(f.name)

# Add new fields if needed
if not u"DF" in existingFields:
    arcpy.AddField_management(out_strlink_fc, "DF", "DOUBLE", "25", "1", "",
                              "", "NULLABLE", "NON_REQUIRED")

if not u"DS_MIX" in existingFields:
    arcpy.AddField_management(out_strlink_fc, "DS_MIX", "LONG", "9", "0", "",
                              "", "NULLABLE", "NON_REQUIRED")

if not u"TRIB" in existingFields:
    arcpy.AddField_management(out_strlink_fc, "TRIB", "LONG", "9", "0", "",
                              "", "NULLABLE", "NON_REQUIRED")

fields = ["GridID","HydroID","NextDownID", "DF", "DS_MIX", "TRIB"]

# iterate through the stream fc and calculate dilution
with arcpy.da.UpdateCursor(out_strlink_fc, fields) as Inrows:
    for row in Inrows:
        
        trib_gid = hidDict[row[1]]["GridID"]
        down_hid = row[2]
        
        if down_hid == -1:
            # we are at the watershed outlet
            df = -1
            down_mix = -1
            trib = gidDict[trib_gid]["MAX"]
        else:
            down_gid = hidDict[down_hid]["GridID"]
            trib = gidDict[trib_gid]["MAX"]
            down_mix = gidDict[down_gid]["MIN"]           
            df = down_mix / trib
            
        row[3] = df
        row[4] = down_mix
        row[5] = trib
        Inrows.updateRow(row)

print("8b. dilution factors calculated")

# ---- SSBT streams ---------------------------------------------------------

#focal 3x3 sum of ssbt raster
if arcpy.Exists(out_ssbt_focal) is False:
    out_focal = FocalStatistics(in_ssbt_raster, NbrRectangle(3, 3, "CELL"),"SUM","DATA")
    out_focal.save(out_ssbt_focal)
print("9. ssbt focal sum done")

# product of 3x3 focal sum and s05_str
if arcpy.Exists(out_ssbt_product) is False:
    out_product = arcpy.Raster(out_ssbt_focal) * arcpy.Raster(out_str_raster)
    out_product.save(out_ssbt_product)
print("10. ssbt product done")

# select only cells along strlink where con vlaue >=1
if arcpy.Exists(out_ssbt_strlink) is False:
    out_con = Con(out_ssbt_product, out_strlink_raster, where_clause="Value >= 1")
    out_con.save(out_ssbt_strlink)
print("11. ssbt con done")

# convert to feature class
if arcpy.Exists(out_ssbt_fc) is False:
    ArcHydroTools.DrainageLineProcessing(in_link_raster=out_ssbt_strlink, 
                                     in_flow_direction_raster=out_fdr, 
                                     out_drainageline_features=out_ssbt_fc)
    
    arcpy.AddField_management(out_ssbt_fc, "TYPE", "TEXT", "",
                              "", 25, "",
                              "NULLABLE", "NON_REQUIRED")
    
    proj = arcpy.Describe(out_ssbt_fc).SpatialReference 
    with arcpy.da.UpdateCursor(out_ssbt_fc,["TYPE"],"", proj) as cursor:
        for row in cursor:
            row[0] = "SSBT"
            cursor.updateRow(row)    
print("12. ssbt polyline done")

if arcpy.Exists(out_upstream_fc) is False:
    arcpy.Erase_analysis(in_features=out_strlink_fc, erase_features=out_ssbt_fc, 
                        out_feature_class=out_upstream_fc, 
                        cluster_tolerance=None)
print("13. upstream polyline done")

# ----- Type N ---------------------------------------------------------

#focal 3x3 sum of ssbt raster
if arcpy.Exists(out_typef_focal) is False:
    out_focal = FocalStatistics(in_typef_raster, NbrRectangle(3, 3, "CELL"),"SUM","DATA")
    out_focal.save(out_typef_focal)
print("14. type f focal sum done")

# product of 3x3 focal sum and s05_str
if arcpy.Exists(out_typef_product) is False:
    out_product = arcpy.Raster(out_typef_focal) * arcpy.Raster(out_str_raster)
    out_product.save(out_typef_product)
print("15. type f product done")

# select only cells along strlink where con vlaue >=1
if arcpy.Exists(out_typef_strlink) is False:
    out_con = Con(out_typef_product, out_strlink_raster, where_clause="Value >= 1")
    out_con.save(out_typef_strlink)
print("16. type f con done")

# convert to feature class
if arcpy.Exists(out_typef_fc) is False:
    ArcHydroTools.DrainageLineProcessing(in_link_raster=out_typef_strlink, 
                                     in_flow_direction_raster=out_fdr, 
                                     out_drainageline_features=out_typef_fc)
print("17. type f polyline done")
    
# ----- Type N ---------------------------------------------------------
if arcpy.Exists(out_typen_upstream_fc) is False:
    arcpy.Erase_analysis(in_features=out_strlink_fc, erase_features=out_typef_fc, 
                        out_feature_class=out_typen_upstream_fc, 
                        cluster_tolerance=None)
    
    arcpy.AddField_management(out_typen_upstream_fc, "TYPE", "TEXT", "",
                              "", 25, "",
                              "NULLABLE", "NON_REQUIRED")
    with arcpy.da.UpdateCursor(out_typen_upstream_fc,["TYPE"],"", proj) as cursor:
        for row in cursor:
            row[0] = "Type N"
            cursor.updateRow(row)    
    
print("18. type n polyline done")

# ----- Non SSBT Type F ------------------------------------------------

if arcpy.Exists(out_typef_non_ssbt) is False:
    arcpy.Erase_analysis(in_features=out_upstream_fc, erase_features=out_typen_upstream_fc, 
                        out_feature_class=out_typef_non_ssbt, 
                        cluster_tolerance=None)
    arcpy.AddField_management(out_typef_non_ssbt, "TYPE", "TEXT", "",
                              "", 25, "",
                              "NULLABLE", "NON_REQUIRED")
    with arcpy.da.UpdateCursor(out_typef_non_ssbt,["TYPE"],"", proj) as cursor:
        for row in cursor:
            row[0] = "Type N"
            cursor.updateRow(row)    
print("19. non ssbt type f polyline done")

# ----- Final upstream Merge ---------------------------------------------

if arcpy.Exists(out_upstream_merge) is False:
    arcpy.Merge_management([out_typen_upstream_fc, out_typef_non_ssbt],
                           out_upstream_merge)
print("20 upstream merge done")  
    
if arcpy.Exists(out_upstream_final_fc) is False:   
    dis_fields = ["HydroID", "GridID", "NextDownID", "DF", "DS_MIX", "TRIB", "TYPE"]
    arcpy.Dissolve_management(in_features=out_upstream_merge,
                              out_feature_class=out_upstream_final_fc, 
                             dissolve_field=dis_fields, 
                             statistics_fields=None, 
                             multi_part="MULTI_PART", 
                             unsplit_lines="DISSOLVE_LINES")
print("21 final upstream dissolve done")

# ---- Generate Nodes for splitting -------------------------------------
    
if arcpy.Exists(out_split_nodes_fc) is False:
    # Get the spatial projecton of the input stream lines
    proj = arcpy.Describe(out_upstream_final_fc).SpatialReference    
    
    if checkDirection is True:
        proj_ele = arcpy.Describe(in_dem).spatialReference
    
        # Check to make sure the  elevation raster and input 
        # streams are in the same projection.
        if proj.name != proj_ele.name:
            arcpy.AddError("{0} and {1} do not ".format(nodes_fc,z_raster)+
                           "have the same projection."+
                           "Please reproject your data.")
            sys.exit("Input stream line and elevation raster do not have "
                     "the same projection. Please reproject your data.")
    
    # Create the stream nodes and return them as a list
    nodeList, attrList = create_node_list(out_upstream_final_fc, out_ssbt_fc, checkDirection, in_dem, node_dx)
    
    # sort the list by hydro ID and then meters to ssbt
    nodeList = sorted(nodeList, key=itemgetter(1,7), reverse=True)
        
    # Create the output node feature class with the nodes list
    splitfields = ["NODE_ID", "HydroID","GridID","NextDownID",
                    "DF", "DS_MIX", "TRIB",
                    "M_FROM_SSBT", "JUNC_TO_SSBT", "STREAM_AZMTH",
                    "LONGITUDE","LATITUDE"]     
    create_nodes_fc(nodeList, out_split_nodes_fc, out_upstream_final_fc, splitfields, proj)
    
    attrfields = ["M_FROM_SSBT", "JUNC_TO_SSBT", "STREAM_AZMTH",
                   "LONGITUDE","LATITUDE"]     
    create_nodes_fc(attrList, out_attr_nodes_fc, out_upstream_final_fc, attrfields, proj)
print("23. nodes done")


if arcpy.Exists(out_upstream_split_fc) is False:
    arcpy.SplitLineAtPoint_management(out_upstream_final_fc, out_split_nodes_fc, out_upstream_split_fc, "1 Foot")
print("24. split done")

if arcpy.Exists(out_upstream_attr_fc) is False:
    arcpy.SpatialJoin_analysis(target_features=out_upstream_split_fc, join_features=out_attr_nodes_fc, 
                              out_feature_class=out_upstream_attr_fc, 
                              join_operation="JOIN_ONE_TO_ONE", 
                              join_type="KEEP_ALL", 
                              match_option="INTERSECT", 
                              search_radius="0.1 Feet")
print("25. spatial join done")

buffer_out_list = []
for buffer in buffer_widths:
    buffer_out_list.append(target_gdb+r"\s26_buffer_{0}".format(buffer))
    out_buffer_fc = target_gdb + r"\s26_buffer_{0}".format(buffer)
    
    if arcpy.Exists(out_buffer_fc) is False:
        arcpy.Buffer_analysis(in_features=out_upstream_attr_fc, out_feature_class=out_buffer_fc, 
                             buffer_distance_or_field=str(buffer)+" Feet", 
                             line_side="FULL", 
                             line_end_type="FLAT")
    print("26. buffer {0} done".format(buffer))
    
print("done")


