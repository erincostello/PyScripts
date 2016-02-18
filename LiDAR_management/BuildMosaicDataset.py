from __future__ import print_function
import arcpy
import os
import csv
from osgeo import ogr, gdal

incsvfile = r"\\DEQWQNAS01\Lidar06\OLC_LANE_COUNTY_2014\path_new_HH_rasters.csv"
outcsvfile = r"\\DEQWQNAS01\Lidar06\OLC_LANE_COUNTY_2014\path_new_HH_rasters.csv"
mdname = r"\\DEQWQNAS01\Lidar07\Willamette.gdb\HH"

#incsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_HH_rasters.csv"
#outcsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_HH_rasters.csv"
#mdname = r"\\DEQWQNAS01\Lidar07\Willamette.gdb\HH"

#incsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_VH_rasters.csv"
#outcsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_VH_rasters.csv"
#mdname = r"\\DEQWQNAS01\Lidar07\Willamette.gdb\VH"

status_col = 0
name_col = 1
path_col = 2
clean_col = 4

geofilter = False

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

def geo_filter(raster_list, geo_field_name, geo_area, clean_col):
    '''Removes rows that have quad names that are not within
    the specified geo area'''
    
    # Read in the data
    driver = ogr.GetDriverByName("OpenFileGDB")
    db = driver.Open(r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\QUADS.gdb", 0)
    fc = db.GetLayer("WBD_HU06_HUC12_Quadindex7_5")
    
    # Pull the feature with the query
    fc.SetAttributeFilter("{0} = {1}".format(geo_field_name, geo_area))
    
    # Pull the quads
    quads = [feature.GetField("OHIOCODE") for feature in fc]
    
    # Get all the unique values
    myquads = set(quads)
       
    keep_rasters = []
    for row in raster_list:
        
        # Identify if the name is an ohio code eg "vh45123d4"
        if (len(row[clean_col]) == 9 and
            row[clean_col][0:1].isalpha() is True and
            row[clean_col][2:6].isdigit() is True and
            row[clean_col][7].isalpha() is True and
            row[clean_col][8].isdigit() is True):
            
            if any(quad.lower() in row[clean_col] for quad in myquads):
                keep_rasters.append(row)
        else:
            # not an ohio code, keep anyway
            keep_rasters.append(row) 
    
    return keep_rasters

csvlist =  read_csv(incsvfile, skipheader=False)
keep_quads = []

if geofilter is True:
    keep_quads = geo_filter(csvlist, geo_field_name, geo_area, clean_col)
    
    print("Output filtered quad list to csv")
    write_csv(keep_quads, outcsvfile)    

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
    if row[status_col] == "X":
        n = n + 1
    else:
        inpath = row[2]
        print("mosaicing "+str(n)+" of "+str(tot)+" "+inpath)
        arcpy.AddRastersToMosaicDataset_management(
             mdname,  rastype, inpath, updatecs, updatebnd, updateovr,
             maxlevel, maxcs, maxdim, spatialref, inputdatafilter,
             subfolder, duplicate, buildpy, calcstats, 
             buildthumb, comments, forcesr)
        keep_quads[n][status_col] = "X"
        write_csv(keep_quads, outcsvfile)
        n = n + 1
print("done")
