#######################################################################################
# This generates the ownership class raster
# v1.0
# 
#
# Ryan Michie
#######################################################################################

from __future__ import print_function
import arcpy
from arcpy import env
from arcpy.sa import *

# Check out the ArcGIS Spatial Analyst extension license
arcpy.CheckOutExtension("Spatial")


env.workspace = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\Ownership.gdb"
env.overwriteOutput = True

westfor = env.workspace + r"\Western_For_OWNCLASS_ssn"
westfor_con = env.workspace + r"\Western_For_OWNCLASS_ssn_con"
westfor_rc = env.workspace + r"\Western_For_OWNCLASS_ssn_rc"
nlcd = env.workspace + r"\NLCD2011_ssn"
rsa = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\Hydro\Hydro.gdb\RSA_SSN_RID_30m"
rca = r"C:\WorkSpace\Biocriteria\WatershedCharaterization\SSN\Hydro\Hydro.gdb\RCA_RID_30m"
out_rsa_table = env.workspace + r"\tbl_OWNRSA_by_RID_sqmeters"
out_rca_table = env.workspace + r"\tbl_OWNRCA_by_RID_sqmeters"

# ------------------------------------------------------------------------
# Create the raster that replaces PNI (Value = 1) with the NLCD 2011 values 
print("con")
if arcpy.Exists(westfor_con) == False:
    con1 = Con(Raster(westfor)==1, Raster(nlcd), Raster(westfor))
    con1.save(westfor_con)
else:
    con1 = Raster(westfor_con)
    
# ------------------------------------------------------------------------
# Reclass the values
print("reclass")
if arcpy.Exists(westfor_rc) == False:
    # Final Reclass
    # 1 = PNI FOREST
    # 2 = STATE FOREST
    # 3 = PI FOREST
    # 4 = MISC
    # 8 = FEDERAL FOREST
    # 9 = URBAN
    # 10= AG
    rc = RemapValue([[2,2],[3,3],[4,4],[5,8],[6,"NoData"],
                     [7,8],[11,"NoData"],[12,1],[21,1],[22,9],[23,9],[24,9],
                     [31,1],[41,1],[42,1],[43,1],[52,1],[71,1],[81,10],
                     [82,10],[90,1],[95,1]])
    rc1 = Reclassify(con1, "Value", rc)
    rc1.save(westfor_rc)
    print("done")
    
# ------------------------------------------------------------------------
# Tabulate by area
print("tabulate area")
if arcpy.Exists(out_rsa_table) == False:
    TabulateArea(Raster(rsa), "rid", westfor_rc, "Value", out_rsa_table)

if arcpy.Exists(out_rca_table) == False:
    TabulateArea(Raster(rca), "rid", westfor_rc, "Value", out_rca_table)

# ------------------------------------------------------------------------
# Add new field names, copy values, delete old fields
print("Add/Delete fields")

rcafields = [ "OWNRCA_PRI", "OWNRCA_ODF", "OWNRCA_FED", "OWNRCA_URB", "OWNRCA_AGR"]
rsafields = [ "OWNRSA_PRI", "OWNRSA_ODF", "OWNRSA_FED", "OWNRSA_URB", "OWNRSA_AGR"]
delrcafields = arcpy.ListFields(out_rsa_table,"VALUE*","All")
delrsafields = arcpy.ListFields(out_rsa_table,"VALUE*","All")

fdict = {"OWNRCA_PRI": "!VALUE_1! + !VALUE_3!",
         "OWNRCA_ODF": "!VALUE_2!",
         "OWNRCA_FED": "!VALUE_8!",
         "OWNRCA_URB": "!VALUE_9!",
         "OWNRCA_AGR": "!VALUE_10!",
         "OWNRSA_PRI": "!VALUE_1! + !VALUE_3!",
         "OWNRSA_ODF": "!VALUE_2!",
         "OWNRSA_FED": "!VALUE_8!",
         "OWNRSA_URB": "!VALUE_9!",
         "OWNRSA_AGR": "!VALUE_10!"}

for i in range(0,len(rcafields)):
    arcpy.AddField_management(out_rca_table, rcafields[i], "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED")
    arcpy.AddField_management(out_rsa_table, rsafields[i], "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED")
    
    arcpy.CalculateField_management(out_rca_table, rcafields[i], fdict[rcafields[i]], "PYTHON_9.3")
    arcpy.CalculateField_management(out_rsa_table, rsafields[i], fdict[rsafields[i]], "PYTHON_9.3")

for field in delrcafields:
    arcpy.DeleteField_management(out_rca_table, [field.name])
    
for field in delrsafields:
    arcpy.DeleteField_management(out_rsa_table, [field.name])