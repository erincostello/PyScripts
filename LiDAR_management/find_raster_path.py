
# This script walks directories looking for bare earth (BE), 
# hightest hit (HH), or vegetation height (VH) raster data. It makes an 
# inventory of the raster location for each raster type, the year it 
# was collected, cleans up the file name, and reconciles naming conflicts.
# It also filters based on geographic locations.

# The output is a csv information with organized this way:
# header = ["STATUS", "NAME", "PATH", "PROJECT", "YEAR", "NAMECLEAN", "NAMENEW", "TYPE"]

# 0 Processing status
# 1 Raster Name
# 2 path to raster
# 3 the AOI project name
# 4 Year LiDAR was acquired
# 5 NameClean
# 6 NewName
# 7 image

import arcpy
import os
import csv
import string
from osgeo import ogr
from osgeo import gdal
from collections import defaultdict
from operator import itemgetter

# output csv files, (if these files already exist)
csv_be = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_new2_BE_rasters.csv"
csv_hh = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_new2_HH_rasters.csv"
csv_vh = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Willamette_new2_VH_rasters.csv"

# input to use as an existing raster_list
#in_be_shp =  r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWilamette\VH_footprints_20150316.shp"
#in_hh_shp =
#in_vh_shp = 

# input csv file indicating which year the project was flown
csv_year =  r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_by_year_20150825.csv"

# search and replace strings for veght (some files use the longer prefix)
str_search_list = ["veght", "veg_height"]
replace_str = "vh"

# strings to identify different rasters types
keep_be = ["be", "bare"]
keep_hh = ["hh", "high"]
keep_vh = ["vh", "veght", "veg_height"]

# ouput csv header
header = ["STATUS", "NAME", "PATH", "PROJECT", "YEAR", "NAMECLEAN", "NAMENEW", "TYPE"]

# output column assignments
status_col = 0
name_col = 1
path_col = 2
proj_col = 3
year_col = 4
clean_col = 5
new_name_col = 6
type_col = 7

# if overwrite_csv = False an existing output csv should be present 
# it reads in the data and appends any new data found 
# It does not check for duplicate paths
overwrite_csv = True

cleannames = True
newnames = True
geofilter = True

geo_field_name = "HUC_8"
geo_area = "'17090001','17090002','17090003','17090004','17090005','17090006'"

# List of directories to search
#workspaces = [r"\\DEQWQNAS01\Lidar01",
        #r"\\DEQWQNAS01\Lidar02",
        #r"\\DEQWQNAS01\Lidar03",
        #r"\\DEQWQNAS01\Lidar04",
        #r"\\DEQWQNAS01\Lidar05",
        #r"\\DEQWQNAS01\Lidar06"]
        
workspaces = [r"\\DEQWQNAS01\Lidar01\PDX-MTHood",
        r"\\DEQWQNAS01\Lidar01\WillametteValley",
        r"\\DEQWQNAS01\Lidar03\Blue_River\Other_Products\OGIC",
        r"\\DEQWQNAS01\Lidar03\Central_Coast_Range",
        r"\\DEQWQNAS01\Lidar03\HJAndrews\Other_Products\OGIC",
        r"\\DEQWQNAS01\Lidar03\OLC_CLACKAMOLE_2013",
        r"\\DEQWQNAS01\Lidar04\NorthCoast",
        r"\\DEQWQNAS01\Lidar05\2012_FallCreek_MiddleFork\RASTERS\OGIC",
        r"\\DEQWQNAS01\Lidar05\OLC_GREEN_PETER_2012",
        r"\\DEQWQNAS01\Lidar05\OLC_SCAPPOOSE_2013",
        r"\\DEQWQNAS01\Lidar05\OLC_TILLAMOOK_YAMHILL_2012",
        r"\\DEQWQNAS01\Lidar05\OLC_YAMBO_2010",
        r"\\DEQWQNAS01\Lidar06\OLC_LANE_COUNTY_2014"]

# Disregard any folder with the name in the ignore list
ignore = ["POINT", "REPORT", "LAS", "LAZ", "VEC", "SHAP", "ASC", "TIN","INTEN",
          "DEN","HILLS","HL", "HILSD", "HS", "ORTHO", "PHOTO","TRAJ", "RECYCLER",
          "System Volume Information","Lower_Columbia","USFS_Original",
          "Yamhill_DEQ","Deschutes_from_USFS_old", "XXX"]

def build_raster_list_from_shp(in_shp):
    """Builds a sorted list of each raster to be processed.
    shp must contain fields titled Year, Path, Name, NameClean, and NameNew"""
    
    # Read the shapefile
    source = ogr.Open(in_shp, 1)
    fc = source.GetLayer()
    # Pull the path, year, and raster file name. 
    # The second name is a new name when there are duplicates
    raster_list = [[feature.GetField("Year"),
                  feature.GetField("Path"),
                  feature.GetField("Name"),
                  feature.GetField("NameClean"),
                  feature.GetField("NameNew")] for feature in fc]
    source = None
    
    ## Add a cols for processing status, sort order, and raster format
    raster_list = [["#"] + raster_list[n] + ["#"] for n in range(0, len(raster_list))]
    
    # sort the list by year and then NewName
    #raster_list = sorted(raster_list, key=itemgetter(0, 4), reverse=False) 
    
    return(raster_list)

def  build_raster_list_from_csv(csvfile, status_col, name_col, path_col,
                                year_col, proj_col, name_clean_col,
                                new_name_col, type_col):
    """Read from an existing csv, and pull infor for each raster to be
    processed into a sorted list. csv must contain columns with this info
    Processing status, file name, directory path, year, project name,
    Name Clean, and Name New, file type."""
    csv_list = read_csv(csvfile, skipheader = True)
    # Pull the path, year, and raster file name. 
    raster_list = [[row[status_col],
                    row[name_col],
                    row[path_col],
                    row[year_col],
                    row[proj_col], 
                    row[name_clean_col],
                    row[new_name_col],
                    row[type_col]] for row in csv_list]
        
    return(raster_list)


def read_csv_dict(csvfile, key_col, value_col, skipheader = True):
    """Reads an input csv file and returns a dictionary with
    one of the columns as the dictionary keys and another as the values"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader == True: reader.next()
        csvdict = dict((row[key_col],row[value_col]) for row in reader)
    return csvdict

def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the data as a list"""
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

def get_index_of_duplicate_names(name_list):
    dupdict = defaultdict(list)
    for i, item in enumerate(name_list):
        dupdict[item].append(i)
    return ((indx) for key, indx in dupdict.items() if len(indx)>1)

def clean_names(raster_list, name_col, year_col, clean_col):
    '''Cleans up the filename putting everything in lower case, removes
    underscores, and strips unique alpha letters from the end of ohio code
    quad names'''
    
    # Check to see if the list is empty
    if raster_list:
        # Clean up the name and copy into a new list
        for i in range(0, len(raster_list)):
            mod_name1 = raster_list[i][name_col].lower()
            mod_name1 = mod_name1.replace("_", "")
            for this_string in str_search_list:
                mod_name1 = mod_name1.replace(this_string, replace_str)
            mod_name1 = mod_name1.split('.',1)[0]
            
            # Identify if the name is an ohio code and has a letter at the end eg "vh45123d4a"          
            if (len(mod_name1) == 10 and
                    mod_name1[0:1].isalpha() is True and
                    mod_name1[2:6].isdigit() is True and
                    mod_name1[7].isalpha() is True and
                    mod_name1[8].isdigit() is True and
                    mod_name1[9].isalpha() is True):
                
                # Remove letter at end if it has one "vh45123d4"
                raster_list[i][clean_col] =  mod_name1[:-1]
            else:
                raster_list[i][clean_col] = mod_name1
                
    return raster_list

def new_names(raster_list, year_col, clean_col, new_name_col):
    '''Reconciles duplicate quad names and assigns an alpha letter
    at the end of the string starting with the oldest collected raster.
    Recognizes existing quad names and names new ones accordingly.'''
       
    # Sort by modifid file name, then year
    raster_list = sorted(raster_list, key=itemgetter(clean_col, year_col), reverse=False)
    
    # Make a list of just the clean names
    clean_list = [row[clean_col] for row in raster_list]
    
    # Make a list holding True/False if the new name col is None
    none_list = [row[new_name_col] is None for row in raster_list]
    
    # Add the clean name to new name field for all None elements
    for i in range(0,  len(raster_list)):
        if none_list[i] is True:
            raster_list[i][new_name_col] = clean_list[i]

    # Find the duplicates and add a letter at the end 
    # staring with the oldest collected raster
    duplist = get_index_of_duplicate_names(clean_list)
    
    for dup in sorted(get_index_of_duplicate_names(clean_list)):
        for i in range(0, len(dup)):
            # Check if the element is None so we don't 
            # accidently overwrite an existing new name
            if none_list[dup[i]]:
                mod_name2 = clean_list[dup[i]]
                new_name = mod_name2 + string.ascii_lowercase[i]
                raster_list[dup[i]][new_name_col] = new_name
            
    return raster_list

def geo_filter(raster_list, geo_field_name, geo_area, clean_col):
    '''Removes rows that have quad names that are not within
    the specified geo area'''
    
    # Read in the data
    driver = ogr.GetDriverByName("OpenFileGDB")
    db = driver.Open(r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\QUADS.gdb", 0)
    fc = db.GetLayer("WBD_HU06_HUC12_Quadindex7_5")
    
    # Pull the feature with the query
    fc.SetAttributeFilter("{0} IN ({1})".format(geo_field_name, geo_area))
    
    # Pull the quads
    quads = [feature.GetField("OHIOCODE") for feature in fc]
    
    # Get all the unique values
    myquads = sorted(set(quads), reverse=False)
       
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

rasters_be = []
rasters_hh = []
rasters_vh = []
yeardict = read_csv_dict(csv_year, key_col=0, value_col=2, skipheader=True)
projdict = read_csv_dict(csv_year, key_col=0, value_col=1, skipheader=True)

if overwrite_csv is False:
    rasters_be = build_raster_list_from_csv(csv_be, status_col, name_col,
                                            path_col, year_col, proj_col,
                                            name_clean_col, new_name_col,
                                            type_col)
    
    rasters_hh = build_raster_list_from_csv(csv_hh, status_col, name_col,
                                            path_col, year_col, proj_col,
                                            name_clean_col, new_name_col,
                                            type_col)
    
    rasters_vh = build_raster_list_from_csv(csv_vh, status_col, name_col,
                                            path_col, year_col, proj_col,
                                            name_clean_col, new_name_col,
                                            type_col)
    
for workspace in workspaces:
    for dirpath, dirnames, filenames in arcpy.da.Walk(workspace,
                                                      topdown=True,
                                                      datatype="RasterDataset"):                
        remove_ = []
        print(dirpath)
        for d in dirnames:
            if any(word.lower() in d.lower() for word in ignore):
                remove_.append(d)
        
        for r in remove_:
            dirnames.remove(r)        
                    
        if any(word.lower() in dirpath.lower() for word in keep_be):    
            for filename in filenames:
                if all(word.lower() not in filename.lower() for word in ignore):
                    year = [value for key, value in yeardict.items() if dirpath.startswith(key)]
                    proj = [value for key, value in projdict.items() if dirpath.startswith(key)]
                    
                    if not year:
                        year = ["NA"]
                        proj = ["NA"]
                    rasters_be.append(["#", filename, os.path.join(dirpath, filename), proj[0], year[0], None, None, "#"])
                
        if any(word.lower() in dirpath.lower() for word in keep_hh):   
            for filename in filenames:
                if all(word.lower() not in filename.lower() for word in ignore):
                    year = [value for key, value in yeardict.items() if dirpath.startswith(key)]
                    proj = [value for key, value in projdict.items() if dirpath.startswith(key)]
                    
                    if not year:
                        year = ["NA"]
                        proj = ["NA"]
                    rasters_hh.append(["#", filename, os.path.join(dirpath, filename), proj[0], year[0], None, None, "#"])
        
        if any(word.lower() in dirpath.lower() for word in keep_vh):   
            for filename in filenames:
                if all(word.lower() not in filename.lower() for word in ignore):
                    year = [value for key, value in yeardict.items() if dirpath.startswith(key)]
                    proj = [value for key, value in projdict.items() if dirpath.startswith(key)]
                    
                    if not year:
                        year = ["NA"]
                        proj = ["NA"]
                    rasters_vh.append(["#", filename, os.path.join(dirpath, filename), proj[0], year[0], None, None, "#"])        

# check for duplicate names
if cleannames is True:
    rasters_be = clean_names(rasters_be, name_col, year_col, clean_col)
    rasters_hh = clean_names(rasters_hh, name_col, year_col, clean_col)
    rasters_vh = clean_names(rasters_vh, name_col, year_col, clean_col)

if newnames is True:
    rasters_be = new_names(rasters_be, year_col, clean_col, new_name_col)
    rasters_hh = new_names(rasters_hh, year_col, clean_col, new_name_col)
    rasters_vh = new_names(rasters_vh, year_col, clean_col, new_name_col)

if geofilter is True:
    rasters_be = geo_filter(rasters_be, geo_field_name, geo_area, clean_col)
    rasters_hh = geo_filter(rasters_hh, geo_field_name, geo_area, clean_col)
    rasters_vh = geo_filter(rasters_vh, geo_field_name, geo_area, clean_col)

print("writing to csv")

rasters_be.insert(0, header)
rasters_hh.insert(0, header)
rasters_vh.insert(0, header)

write_csv(rasters_be, csv_be)
write_csv(rasters_hh, csv_hh)
write_csv(rasters_vh, csv_vh)
print("Done")
