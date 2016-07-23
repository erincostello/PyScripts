"""
Adds rasters identifed in a comma delimited text file to an ESRI mosaic
dataset. The text file is produced by running the
script "find_raster_path.py". A mosaic dataset must already exist.
A geo filter function can be used to limit processing to specfic areas
of interest. The rasters can also be copied to a new directory and
renamed based on a field in the text file.

"""

from __future__ import print_function
import arcpy
import os
import csv
from osgeo import ogr, gdal

# -- Start Inputs ------------------------------------------------------

# input comma seperated text file w/ inventory of rasters going into md
incsvfile = r"F:\LiDAR\Mid_Coast\Mid_Coast_md_BE_rasters.csv"
#incsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Mid_Coast_HH_rasters.csv"
#incsvfile = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Mid_Coast_VH_rasters.csv"

# output comma seperated text file w/ inventory of rasters in md 
outcsvfile = r"F:\LiDAR\Mid_Coast\Mid_Coast_md_BE_rasters.csv"
#outcsvfile = r"F:\LiDAR\Mid_Coast\Mid_Coast_md_HH_rasters.csv"
#outcsvfile = r"F:\LiDAR\Mid_Coast\Mid_Coast_md_VH_rasters.csv"

# directory and name of the mosaic dataset 
mdname = r"F:\LiDAR\Mid_Coast\MOSAICS.gdb\BE"
#mdname = r"F:\LiDAR\Mid_Coast\MOSAICS.gdb\HH"
#mdname = r"F:\LiDAR\Mid_Coast\MOSAICS.gdb\VH"

# output column assignments
status_col = 0
name_col = 1
path_col = 2
pjct_col = 3
year_col = 4
proj_col = 5
quad_col = 6
clean_col = 7
new_name_col = 8
format_col = 9

use_geofilter = False
use_newname = True

# copy raster data to a new directory?
use_newdir = True

# the directory where raster data will be copied if 'use_newdir' is True
newdir = r"F:\LiDAR\Mid_Coast\BE"

# output raster format when coping, use "" for ESRI grid 
out_format = ""

# ouput csv header
header = ["STATUS", "NAME", "PATH", "PROJECT", "YEAR", "PROJ", "QUAD", "NAMECLEAN", "NAMENEW", "FORMAT"]

# -- End Inputs --------------------------------------------------------

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the header row and data as a list"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader == True: reader.next()
        csvlist = [row for row in reader]
    return(csvlist)

def write_csv(csvlist, csvheader, write_header, csvfile):
    """write the input list to csv"""
    with open(csvfile, "wb") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(csvheader)        
        for row in csvlist:
            writer.writerow(row) 

def geo_filter(raster_list, geo_field_name, geo_area, quad_col):
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
        
        # Identify if the name is an ohio code eg "vh45123d"
        quad_name = row[quad_col]
        
        if (len(quad_name) == 7 and
            quad_name[0:4].isdigit() and
            quad_name[5].isalpha() and
            quad_name[6].isdigit()):
            
            if any(quad.lower() in quad_name for quad in myquads):
                keep_rasters.append(row)
        else:
            # not an ohio code, keep anyway
            keep_rasters.append(row) 
    
    return keep_rasters

csvlist = read_csv(incsvfile, skipheader=False)

if use_geofilter:
    keep_quads = []    
    keep_quads = geo_filter(csvlist, geo_field_name, geo_area, quad_col)
    
    print("Output filtered quad list to csv")
    write_csv(keep_quads, none, False, outcsvfile)
else:
    # write to output
    write_csv(csvlist, None, False, outcsvfile)

# At this point the csv file should be reimported if any changes are made.
keep_quads = read_csv(outcsvfile, skipheader=True)

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
        inraster = os.path.join(row[path_col], row[name_col])
                
        if use_newdir:
            if use_newname:
                name = row[new_name_col]
            else:
                name = row[name_col]            
            
            out_raster = os.path.join(newdir, name+out_format)
            
            if arcpy.Exists(out_raster) == False:
                print("copying "+str(n)+" of "+str(tot)+" "+inraster)
                arcpy.CopyRaster_management(in_raster=inraster,
                                            out_rasterdataset=out_raster)
            inraster = out_raster
            
        print("mosaicing "+str(n)+" of "+str(tot)+" "+inraster)
        arcpy.AddRastersToMosaicDataset_management(
             mdname,  rastype, inraster, updatecs, updatebnd, updateovr,
             maxlevel, maxcs, maxdim, spatialref, inputdatafilter,
             subfolder, duplicate, buildpy, calcstats, 
             buildthumb, comments, forcesr)
        keep_quads[n][status_col] = "X"
        write_csv(keep_quads, header, True, outcsvfile)
        n = n + 1
print("done")
