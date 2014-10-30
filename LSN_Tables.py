#######################################################################################
# This cleans up the various tables produced by zonal statistics in ArcGIS, adds 
# variable names and joins them into the master edge table
# v1.0
# 
#
# Ryan Michie
#######################################################################################

# Import system modules
from __future__ import print_function
import os
import time
import arcpy
from arcpy import env


edgetable = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\LSN04\Tables.mdb\edges"
env.workspace = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\LSN04\Tables.mdb"

# list of varibale tables
tbl_list = ["tbl_LITH_COMP_catch_sq_meters_rid_Tabulations",
 "tbl_LITH_COMP_stream45m_sq_meters_rid_Tabulations",
 "tbl_LITH_EROD_catch_sq_meters_rid_Tabulations",
 "tbl_LITH_EROD_stream45m_sq_meters_rid_Tabulations",
 "tbl_SOIL_KFACTWS_0_18in_rid_Tabulations",
 "tbl_SOIL_CLAYP_rid_Tabulations",
 "tbl_SOIL_SANDP_rid_Tabulations",
 "tbl_SOIL_SILT_CLAYP_rid_Tabulations",
 "tbl_SOIL_SILTP_rid_Tabulations",
 "tbl_SPLASH_count_rid_Tabulations",
 "tbl_SUSCEP_10mDEM_rid_Tabulations_sqmeters",
 "tbl_SUSCEP_LiDAR_rid_Tabulations_sqmeters",
 "tbl_ROADS",
 "tbl_SINUMAP_by_RID",
 "tbl_POPRCA2010_by_RID",
 "tbl_OWNRCA_by_RID_sqmeters",
 "tbl_OWNRSA_by_RID_sqmeters"]


#-----------------------------------------------------------------------------
# update the field names in the soil tables by adding a new field and giving
# it the correct name. Then copy over the values from the SUM field into the 
# new field

tbl_soils = [ "tbl_SOIL_KFACTWS_0_18in_rid_Tabulations",
 "tbl_SOIL_CLAYP_rid_Tabulations",
 "tbl_SOIL_SANDP_rid_Tabulations",
 "tbl_SOIL_SILT_CLAYP_rid_Tabulations",
 "tbl_SOIL_SILTP_rid_Tabulations",]
soil_fields = ["KFACTRCA","CLAYRCA","SANDRCA","SILT_CLAYRCA","SILTRCA"]

i = 0
for tbl in tbl_soils:
    arcpy.AddField_management(tbl, soil_fields[i] , "DOUBLE")
    arcpy.CalculateField_management(tbl, soil_fields[i], '!SUM_!', "PYTHON_9.3")       
    i = i + 1

#-----------------------------------------------------------------------------
# This takes the list of all the tables and joins them to the edge table.
# I make sure certian fields are not joined.

for tbl in tbl_list:
    tbl_fieldnames = []
    tbl_keep_fields = []
    fields = arcpy.ListFields(tbl,"*","All")
    for field in fields:
        if field.name.upper() == u"RID":
            join_field = field.name
        if field.name.upper() not in [u"RID", u"rid", u"OBJECTID", u"OBJECTID_1", u"Shape_Length", u"SUM_", u"SUM"]:
            tbl_keep_fields.append(field.name)
        tbl_fieldnames.append(field.name)
    
    print("Joining %s"  %tbl )    
    arcpy.JoinField_management(edgetable, "rid", tbl, join_field, tbl_keep_fields)

#-----------------------------------------------------------------------------
# This adds the disturbance tables
env.workspace = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\Disturbance.gdb"


# build lists of the disturbance tables names and fields
reachtype = ["RCA", "RSA"]
durlist = ["1", "3", "10"]
yearlist = [str(x) for x in range(1996,2009)]

disturbtables = ["tbl_"+ r + "_DISTURB_" + d + "yr_" + y + "_sqm_by_RID" for r in reachtype for d in durlist for y in yearlist]
disturb_fields = ["DIS" + r + "_" + d + "YR_" + y for r in reachtype for d in durlist for y in yearlist]
del(reachtype, durlist, yearlist)

# Iterate through each table, add a new field and give it the varibale name, then copy
# it over. Finally join the table to the edge table.

i = 0
for tbl in disturbtables:
    tbl_fieldnames = []
    tbl_keep_fields = []
    fields = arcpy.ListFields(tbl,"*","All")
    arcpy.AddField_management(tbl, disturb_fields[i] , "LONG")
    arcpy.CalculateField_management(tbl, disturb_fields[i], '!VALUE_1!', "PYTHON_9.3")
    for field in fields:
        if field.name.upper() == u"RID":
            join_field = field.name
        if field.name.upper() not in [u"RID", u"rid", u"OBJECTID", u"OBJECTID_1", u"VALUE_1", u"SUM_", u"SUM"]:
            tbl_keep_fields.append(field.name)
        tbl_fieldnames.append(field.name)
    
    print("Joining %s"  %tbl )     
    arcpy.JoinField_management(edgetable, "rid", tbl, join_field, tbl_keep_fields)
    i = i + 1