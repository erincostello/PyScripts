"""
Walks directories looking for bare earth (BE), 
hightest hit (HH), or vegetation height (VH) raster data. Makes an 
inventory of the raster location, name, the year it 
was collected, which project it is assocated with, the prjoection,
cleans up the file name, tries to identify the quad, and
reconciles naming conflicts. A geo filter function is used to
limit processing to specfic areas of interest.

Outputs are a comma delimited text files of the raster inventory.
Output fields include: status, name, path, project name, year
projection, Ohio quad name, clean name, new name, raster format.

"""
import arcpy
import os
import csv
import string
from osgeo import ogr
from osgeo import gdal
from collections import defaultdict
from operator import itemgetter

# -- Start Inputs ------------------------------------------------------

# output csv files
csv_be = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Mid_Coast_BE_rasters.csv"
csv_hh = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Mid_Coast_HH_rasters.csv"
csv_vh = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\Mid_Coast_VH_rasters.csv"

# if overwrite_csv = False an existing output csv should be present 
# it reads in the data and appends any new data found 
# It does not check for duplicate paths
overwrite_csv = True
use_newname = True

# input to use as an existing raster_list
#in_be_shp =  r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWilamette\VH_footprints_20150316.shp"
#in_hh_shp =
#in_vh_shp = 

# input comma delimited text file indicating which year the project was flown
csv_year =  r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_by_year_20150825.csv"

# search and replace strings for veght (some files use the longer prefix)
str_search_list = ["veght", "veg_height"]
replace_str = "vh"

# strings to identify different rasters types
keep_be = ["be", "bare"]
keep_hh = ["hh", "high"]
keep_vh = ["vh", "veght", "veg_height"]

# ouput csv header
header = ["STATUS", "NAME", "PATH", "PROJECT", "YEAR", "PROJ", "QUAD", "NAMECLEAN", "NAMENEW", "FORMAT"]

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

# use a geo filter?
use_geofilter = True

geo_field_name = "HUC_8"

# Mid Coast
geo_area = "'17100204','17100205','17100206','17100207'"

# The folders to walk to look for raster data
workspaces = [r"\\DEQWQNAS01\Lidar01\PDX-MTHood",
              r"\\DEQWQNAS01\Lidar01\Yaquina_Block", 
              r"\\DEQWQNAS01\Lidar01\WillametteValley",
              r"\\DEQWQNAS01\Lidar01\SouthCoast",
              r"\\DEQWQNAS01\Lidar03\Central_Coast_Range",
              r"\\DEQWQNAS01\Lidar04\OLC_NORTH_COAST_2009",
              r"\\DEQWQNAS01\Lidar05\OLC_SCAPPOOSE_2013",
              r"\\DEQWQNAS01\Lidar05\OLC_TILLAMOOK_YAMHILL_2012",
              r"\\DEQWQNAS01\Lidar05\OLC_YAMBO_2010",
              r"\\DEQWQNAS01\Lidar06\OLC_LANE_COUNTY_2014"]

# Southern Willamette
#geo_area = "'17090001','17090002','17090003','17090004','17090005','17090006'"

#workspaces = [r"\\DEQWQNAS01\Lidar01\PDX-MTHood",
        #r"\\DEQWQNAS01\Lidar01\WillametteValley",
        #r"\\DEQWQNAS01\Lidar01\Blue_River\Other_Products\OGIC",
        #r"\\DEQWQNAS01\Lidar03\Central_Coast_Range",
        #r"\\DEQWQNAS01\Lidar03\HJAndrews\Other_Products\OGIC",
        #r"\\DEQWQNAS01\Lidar03\OLC_CLACKAMOLE_2013",
        #r"\\DEQWQNAS01\Lidar04\OLC_NORTH_COAST_2009",
        #r"\\DEQWQNAS01\Lidar05\2012_FallCreek_MiddleFork\RASTERS\OGIC",
        #r"\\DEQWQNAS01\Lidar05\OLC_GREEN_PETER_2012",
        #r"\\DEQWQNAS01\Lidar05\OLC_SCAPPOOSE_2013",
        #r"\\DEQWQNAS01\Lidar05\OLC_TILLAMOOK_YAMHILL_2012",
        #r"\\DEQWQNAS01\Lidar05\OLC_YAMBO_2010",
        #r"\\DEQWQNAS01\Lidar06\OLC_LANE_COUNTY_2014"]

# List of directories to search
#workspaces = [r"\\DEQWQNAS01\Lidar01",
    #r"\\DEQWQNAS01\Lidar02",
    #r"\\DEQWQNAS01\Lidar03",
    #r"\\DEQWQNAS01\Lidar04",
    #r"\\DEQWQNAS01\Lidar05",
    #r"\\DEQWQNAS01\Lidar06"]

# -- End Inputs --------------------------------------------------------

# Disregard any folder with the name in the ignore list
ignore = ["POINT", "REPORT", "LAS", "LAZ", "VEC", "SHAP", "ASC", "TIN","INTEN",
          "DEN","HILLS","HL", "HILSD", "HS", "ORTHO", "PHOTO","TRAJ", "RECYCLER",
          "System Volume Information","Lower_Columbia","USFS_Original",
          "Yamhill_DEQ","Deschutes_from_USFS_old", "XXX", ".bnd"]

def nested_dict(): 
    """Build a nested dictionary"""
    return defaultdict(nested_dict)

def  build_raster_list_from_csv(csvfile, status_col, name_col, path_col,
                                pjct_col, year_col, proj_col, quad_col,
                                clean_col, new_name_col, format_col):
    """Read from an existing csv, and pulls info for each raster to be
    processed into a sorted list. csv must contain columns with this info
    Processing status, file name, directory path, project name, year,
    projection, ohio code, Name Clean, Name New, raster file type."""
    
    csv_list = read_csv(csvfile, skipheader = True)
    
    raster_list = [[row[status_col],
                    row[name_col],
                    row[path_col],
                    row[pjct_col],
                    row[year_col],
                    row[proj_col],
                    row[quad_col], 
                    row[clean_col],
                    row[new_name_col],
                    row[format_col]] for row in csv_list]    
        
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

def write_csv(csvlist, csvheader, csvfile):
    """write the input list to csv"""
    with open(csvfile, "wb") as f:
        writer = csv.writer(f)
        writer.writerow(csvheader)        
        for row in csvlist:
            writer.writerow(row)

def get_index_of_duplicate_names(name_list):
    dupdict = defaultdict(list)
    for i, item in enumerate(name_list):
        dupdict[item].append(i)
    return ((indx) for key, indx in dupdict.items() if len(indx)>1)

def clean_name(filename):
    '''Cleans up the filename putting everything in lower case, removes
    underscores, and strips raster prefix and unique alpha letters from
    the end of ohio code quad names'''
    
    name_mod = filename.lower()
    name_mod = name_mod.replace("_", "")
    # remove these raster prefix
    for this_string in ["vh", "veght", "veg_height",
                        "be", "bare",
                        "hh", "high", "q"]:
        
        name_mod = name_mod.replace(this_string, "")
        
    # This removes a file extension e.g. .img
    name_mod = name_mod.split('.',1)[0]
    
    # Identify if the name is an ohio code          
    if (len(name_mod) == 7 and
        name_mod[0:4].isdigit() and
        name_mod[5].isalpha() and
        name_mod[6].isdigit()):
        
        quad_key = name_mod
        
    elif (len(name_mod) == 8 and
          name_mod[0:4].isdigit() and
          name_mod[5].isalpha() and
          name_mod[6].isdigit() and
          name_mod[7].isalpha()):
            
        # Remove letter at end e.g. "45123d4"
        quad_key = name_mod[:-1]
        
    else:
        # Note an Ohio code
        quad_key = name_mod
        
    return quad_key


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
            
            if any(quad.lower() == row[clean_col][2:] for quad in myquads):
                keep_rasters.append(row)
        else:
            # not an ohio code, keep anyway
            keep_rasters.append(row) 
    
    return keep_rasters

rasters_be = []
rasters_hh = []
rasters_vh = []

yeardict = read_csv_dict(csv_year, key_col=0, value_col=2, skipheader=True)
pjctdict = read_csv_dict(csv_year, key_col=0, value_col=1, skipheader=True)

if not overwrite_csv:
    rasters_be = build_raster_list_from_csv(csv_be, status_col, name_col,
                                            path_col, pjct_col, year_col,
                                            proj_col, quad_col,
                                            clean_col, new_name_col,
                                            format_col)
    
    rasters_hh = build_raster_list_from_csv(csv_hh, status_col, name_col,
                                            path_col, pjct_col, year_col,
                                            proj_col, quad_col,
                                            clean_col, new_name_col,
                                            format_col)
    
    rasters_vh = build_raster_list_from_csv(csv_vh, status_col, name_col,
                                            path_col, pjct_col, year_col,
                                            proj_col, quad_col,
                                            clean_col, new_name_col,
                                            format_col)

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
                    pjct = [value for key, value in pjctdict.items() if dirpath.startswith(key)]
                    proj = arcpy.Describe(os.path.join(dirpath, filename)).spatialReference.name
                    
                    if not year:
                        year = ["NA"]
                        pjct = ["NA"]
                        
                    quad_key = clean_name(filename)
                    nameclean = "be" + quad_key
                    
                    rasters_be.append(["#", filename,
                                       dirpath,
                                       pjct[0], year[0], proj,
                                       quad_key, nameclean, None, None])
                
        if any(word.lower() in dirpath.lower() for word in keep_hh):   
            for filename in filenames:
                if all(word.lower() not in filename.lower() for word in ignore):
                    year = [value for key, value in yeardict.items() if dirpath.startswith(key)]
                    pjct = [value for key, value in pjctdict.items() if dirpath.startswith(key)]
                    proj = arcpy.Describe(os.path.join(dirpath, filename)).spatialReference.name
                    
                    if not year:
                        year = ["NA"]
                        pjct = ["NA"]
                        
                    quad_key = clean_name(filename)
                    nameclean = "hh" + quad_key
                    rasters_hh.append(["#", filename,
                                       dirpath,
                                       pjct[0], year[0], proj,
                                       quad_key, nameclean, None, None])
        
        if any(word.lower() in dirpath.lower() for word in keep_vh):   
            for filename in filenames:
                if all(word.lower() not in filename.lower() for word in ignore):
                    year = [value for key, value in yeardict.items() if dirpath.startswith(key)]
                    pjct = [value for key, value in pjctdict.items() if dirpath.startswith(key)]
                    proj = arcpy.Describe(os.path.join(dirpath, filename)).spatialReference.name
                    
                    if not year:
                        year = ["NA"]
                        pjct = ["NA"]
                        
                    quad_key = clean_name(filename)
                    nameclean = "vh" + quad_key    
                    rasters_vh.append(["#", filename,
                                       dirpath,
                                       pjct[0], year[0], proj,
                                       quad_key, nameclean, None, None])

# check for duplicate names
if use_newname:
    rasters_be = new_names(rasters_be, year_col, clean_col, new_name_col)
    rasters_hh = new_names(rasters_hh, year_col, clean_col, new_name_col)
    rasters_vh = new_names(rasters_vh, year_col, clean_col, new_name_col)

if use_geofilter:
    rasters_be = geo_filter(rasters_be, geo_field_name, geo_area, clean_col)
    rasters_hh = geo_filter(rasters_hh, geo_field_name, geo_area, clean_col)
    rasters_vh = geo_filter(rasters_vh, geo_field_name, geo_area, clean_col)

print("writing to csv")
write_csv(rasters_be, header, csv_be)
write_csv(rasters_hh, header, csv_hh)
write_csv(rasters_vh, header, csv_vh)
print("Done")
