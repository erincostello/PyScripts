from __future__ import print_function
import arcpy


#mdnameList = [r"\\DEQWQNAS01\Lidar07\Willamette.gdb\BE"]

mdnameList = [r"\\DEQWQNAS01\Lidar07\Willamette.gdb\BE",
              r"\\DEQWQNAS01\Lidar07\Willamette.gdb\HH",
              r"\\DEQWQNAS01\Lidar07\Willamette.gdb\VH"]

for mdname in mdnameList:
    query = "#"
    method = "RADIOMETRY"
    minval = "-40"
    maxval = "20000"
    nvertice = "-1"
    shrinkdis = "0"
    maintainedge = "#"
    skipovr = "SKIP_DERIVED_IMAGES"
    updatebnd = "UPDATE_BOUNDARY"
    requestsize = "-1"
    minregsize = "#"
    simplify = "#"
    
    print("Building footprints " + mdname)
    arcpy.BuildFootprints_management(
         mdname, query, method, minval, maxval, nvertice, shrinkdis,
         maintainedge, skipovr, updatebnd, requestsize, minregsize, 
         simplify)
print("done")