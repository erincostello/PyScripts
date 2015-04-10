from __future__ import print_function
import arcpy
import os
import csv
from osgeo import ogr, gdal

#incsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_BE_rasters.csv"
#outcsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_BE_rasters.csv"
#mdname = r"\\DEQWQNAS01\Lidar07\Willamette.gdb\BE"

incsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_HH_rasters.csv"
outcsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_HH_rasters.csv"
mdname = r"\\DEQWQNAS01\Lidar07\Willamette.gdb\HH"

#incsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_VH_rasters.csv"
#outcsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_VH_rasters.csv"
#mdname = r"\\DEQWQNAS01\Lidar07\Willamette.gdb\VH"

# Read in the data
driver = ogr.GetDriverByName("OpenFileGDB")
db = driver.Open(r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\QUADS.gdb", 0)
fc = db.GetLayer("WBD_HU06_HUC12_Quadindex7_5")

# Pull the feature with the query
fc.SetAttributeFilter("HU_6_NAME = 'Willamette'")

# Pull the quads
quads = [feature.GetField("OHIOCODE") for feature in fc]

# Get all the unique values
myquads = set(quads)

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the header row and data as a list"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader == True: reader.next()
        csvlist = [row for row in reader]
    return(csvlist)

def write_csv(csvlist, csvfile):
    """write the input list to csv"""
    with open(csvfile, "wb") as f:
        writer = csv.writer(f)
        for row in csvlist:
            writer.writerow(row) 

csvlist =  read_csv(incsvfile, skipheader=False)

keep_quads = []
for row in csvlist:
    if any(quad.upper() in row[0].replace("_", "").upper() for quad in myquads):
        keep_quads.append(["#", row[0].replace("_", "").lower(), row[1]] )

print("Output filtered quad list to csv")
#write_csv(keep_quads, outcsvfile)

# At this point the csv file should be checked and reimported if any changes are made.
keep_quads = read_csv(outcsvfile, skipheader=False)


rastype = "Raster Dataset"
updatecs = "UPDATE_CELL_SIZES"
updatebnd = "NO_BOUNDARY"
updateovr = "NO_OVERVIEWS"
maxlevel = "-1"
maxcs = "#"
maxdim = "#"
spatialref = "#"
inputdatafilter = "#"
subfolder = "NO_SUBFOLDERS"
duplicate = "EXCLUDE_DUPLICATES"
buildpy = "BUILD_PYRAMIDS"
calcstats = "CALCULATE_STATISTICS"
buildthumb = "NO_THUMBNAILS"
comments = "#"
forcesr = "#"

tot = len(keep_quads)
n = 0
for row in keep_quads:
    if row[0] == "X":
        n = n + 1
    else:
        inpath = row[2]
        print("mosaicing "+str(n)+" of "+str(tot)+" "+inpath)
        arcpy.AddRastersToMosaicDataset_management(
             mdname,  rastype, inpath, updatecs, updatebnd, updateovr,
             maxlevel, maxcs, maxdim, spatialref, inputdatafilter,
             subfolder, duplicate, buildpy, calcstats, 
             buildthumb, comments, forcesr)
        keep_quads[n][0] = "X"
        write_csv(keep_quads, outcsvfile)
        n = n + 1
print("done")
