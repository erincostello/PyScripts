# This script builds a land cover code raster from a growth curve raster 
# and LiDAR vegetation height raster and mosaics it into an
# ESRI mosaic dataset
#
# 'csv_lc' is an input csv file with the following col headers:
#    STATUS,   LC_NAME,  LC_PATH,  CODE_PATH,   VH_PATH,    SORT
#    blank,    blank,    blank,    not blank, not blank,   not blank

from __future__ import print_function
import os
import csv
import ntpath
import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

csv_vh = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_new2_VH_rasters.csv"
csv_lc = r"F:\LiDAR\LC\LC_rasters.csv"
status_col = 0
vhpath_col = 8
lcpath = r"F:\LiDAR\LC"
gcpath = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\GrowthCurve.gdb\GCURVE_16bit"

buildpyramids = False
buildmosaic = True
mdname = r"F:\LiDAR\MOSAICS.gdb\LC"

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the header row as a list and the data as a nested dictionary"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader: reader.next()
        csvlist = [row for row in reader]
    return(csvlist)

def write_csv(csvlist, csvfile):
    """write the input list to csv"""
       
    with open(csvfile, "wb") as f:
        writer = csv.writer(f)
        for row in csvlist:
            writer.writerow(row)  

def get_file_name(inpath):
    head, tail = ntpath.split(inpath)
    return tail or ntpath.basename(head)
 
csvlist = read_csv(csv_vh, skipheader=False)

lc_list = [['STATUS','VH_PATH', 'LC_PATH', 'LC_NAME']]

tot = len(csvlist)           
for n, row in enumerate(csvlist):
    
    if n > 0:
        status = row[status_col]
        vhpath = row[vhpath_col]    
                
        # check to see if the lc directory exists already, if not create it
        if not os.path.isdir(lcpath):
            os.mkdir(lcpath)
            
        # make lc code file name by using name of veg height raster
        vhname = get_file_name(vhpath)
        mod_name1 = vhname.lower()
        mod_name1 = mod_name1.replace("_", "")
        mod_name1 = mod_name1.replace("vh", "lc")
        #mod_name1 = mod_name1.replace(".img", "")
        lcname = mod_name1
        lcpathname = lcpath + "\\" + lcname
            
        arcpy.env.snapRaster = vhpath
        
        # check to see if the raster exists
        if not os.path.isfile(lcpathname):
            print("creating "+str(n)+" of "+str(tot)+" "+ lcpathname)
            lc = Plus(gcpath, Int(Con(vhpath < 0, 0, vhpath) + 0.5))
            lc.save(lcpathname)
        
            if buildpyramids:
                print("Building pyramids")        
                arcpy.BuildPyramidsandStatistics_management(lcpathname, 'NONE', 'BUILD_PYRAMIDS', 'CALCULATE_STATISTICS',
                                                        '#', '#', '#', '#', '#', '#', '-1', '#', 'NEAREST', '#', '#', 'SKIP_EXISTING')        
                # Add to a mosaic datset, assumes one already exists
            if buildmosaic and status == "#":
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
                buildpy = "NO_PYRAMIDS"
                calcstats = "CALCULATE_STATISTICS"
                buildthumb = "NO_THUMBNAILS"
                comments = "#"
                forcesr = "#"            
                print("mosaicing "+str(n)+" of "+str(tot)+" "+ lcpathname)
                arcpy.AddRastersToMosaicDataset_management(
                             mdname, rastype, lcpathname, updatecs, updatebnd, updateovr,
                             maxlevel, maxcs, maxdim, spatialref, inputdatafilter,
                             subfolder, duplicate, buildpy, calcstats, 
                             buildthumb, comments, forcesr)
                status = "X"
                
        csvlist[n][status_col] = status            
        line = [status, vhpath, vhname, lcpathname, lcname]
        lc_list.append(line)    
        write_csv(lc_list, csv_lc)
        write_csv(csvlist, csv_vh)

print("done")
