from __future__ import print_function
import os
import csv
import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

csv_vh = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_VH_rasters.csv"
mdname = r"\\DEQWQNAS01\Lidar07\Willamette.gdb\VH"

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the header row as a list and the data as a nested dictionary"""
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
 
csvlist = read_csv(csv_vh, skipheader=False)

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

tot = len(csvlist)
n = 0            
for row in csvlist:
    
    vhname = row[1]
    bepath = row[3]
    hhpath = row[4]
    
    # Check to see if the file is a folder (ESRI grid format), if not we have to move up three directories
    if os.path.isdir(hhpath):
        vhpath = os.path.dirname(os.path.dirname(hhpath))+ "\\VH"
    else:
        vhpath = os.path.dirname(os.path.dirname(os.path.dirname(hhpath)))+ "\\VH"
        
    # check to see if the veght directory exists already, if not create it
    if not os.path.isdir(vhpath):
        os.mkdir(vhpath)
        
    vhpath = vhpath + "\\" +vhname
    csvlist[n][2] = vhpath
    
    # check to see if the raster exists
    if not os.path.isdir(vhpath):
        print("creating "+str(n)+" of "+str(tot)+" "+vhpath)
        vh = Minus(hhpath, bepath)
        vh.save(vhpath)    
    
    if row[0] == "X":
        n = n + 1
    else:    
        # Add to a mosaic datset, assumes one already exists
        print("mosaicing "+str(n)+" of "+str(tot)+" "+vhpath)
        arcpy.AddRastersToMosaicDataset_management(
                     mdname, rastype, vhpath, updatecs, updatebnd, updateovr,
                     maxlevel, maxcs, maxdim, spatialref, inputdatafilter,
                     subfolder, duplicate, buildpy, calcstats, 
                     buildthumb, comments, forcesr)        
        csvlist[n][0] = "X"
        n = n + 1
    write_csv(csvlist, csv_vh)
print("done")