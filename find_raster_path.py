
import arcpy
import os
import csv
import string
from osgeo import ogr
from osgeo import gdal
from collections import defaultdict
from operator import itemgetter

csv_be = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_BE_rasters.csv"
csv_hh = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_HH_rasters.csv"
csv_vh = r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_VH_rasters.csv"
csv_year =  r"\\DEQWQNAS01\Lidar01\OR_INVENTORY\path_by_year_20150313.csv"

def read_csv_dict(csvfile, key_col, value_col, skipheader = True):
    """Reads an input csv file and returns a dictionary with
    one of the columns as the dictionary keys and another as the values"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader == True: reader.next()
        csvdict = dict((row[key_col],row[value_col]) for row in reader)
    return csvdict


def read_csv(csvfile, skipheader = False):
    """Reads an input csv file and returns the header row as a list
    and the data as a nested dictionary"""
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

def clean_names(raster_list, name_col, year_col):
    
    # Clean up the name and copy into a new list
    for i in range(0, len(raster_list)):
        mod_name1 = raster_list[i][name_col].lower()
        mod_name1 = mod_name1.replace("_", "")
        mod_name1 = mod_name1.replace("veght", "vh")
        mod_name1 = mod_name1.split('.',1)[0]
        raster_list[i].append(mod_name1)
        
        #raster_list[i].append(raster_list[i][name_col].lower().replace("_", "").replace("veght", "vh"))
        
    # Get the col index of the new names
    new_index = len(raster_list[0]) - 1
    
    # Identify if the name is an ohio code and has a letter at the end eg "vh45123d4a"
    for row in range(0, len(raster_list)):
        if (len(raster_list[row][new_index]) == 10 and
            raster_list[row][new_index][0:1].isalpha() is True and
            raster_list[row][new_index][2:6].isdigit() is True and
            raster_list[row][new_index][7].isalpha() is True and
            raster_list[row][new_index][8].isdigit() is True and
            raster_list[row][new_index][9].isalpha() is True):
            
            # Remove letter at end if it has one "vh45123d4a"
            raster_list[row][new_index] = raster_list[row][new_index][:-1]
            
    # Sort by modifid name, then year
    raster_list = sorted(raster_list, key=itemgetter(new_index, year_col), reverse=False)
    
    # Make a list of just the modified names
    name_list = [row[new_index] for row in raster_list]    

    # Find the duplicates and add a letter at the end 
    # staring with the oldest collected raster
    duplist = get_index_of_duplicate_names(name_list)
    
    for dup in sorted(get_index_of_duplicate_names(name_list)):
        for i in range(0, len(dup)):
            mod_name2 = name_list[dup[i]]
            new_name = mod_name2 + string.ascii_lowercase[i]
            raster_list[dup[i]][new_index] = new_name
            
    return raster_list

#workspaces = [r"\\DEQWQNAS01\Lidar01",
              #r"\\DEQWQNAS01\Lidar02",
              #r"\\DEQWQNAS01\Lidar03",
              #r"\\DEQWQNAS01\Lidar04",
              #r"\\DEQWQNAS01\Lidar05",
              #r"\\DEQWQNAS01\Lidar06"]
workspaces = [r"\\DEQWQNAS01\Lidar01\PDX-MTHood",
              r"\\DEQWQNAS01\Lidar01\Portland_Pilot",
              r"\\DEQWQNAS01\Lidar01\WillametteValley",
              r"\\DEQWQNAS01\Lidar01\Yaquina_Block",
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
keep_BE = ["BE", "BARE"]
keep_HH = ["HH", "HIGH"]
keep_VH = ["VH", "VEGHT"]

rasters_be = []
rasters_hh = []
rasters_vh = []
yeardict = read_csv_dict(csv_year, key_col=0, value_col=1, skipheader=True)

for workspace in workspaces:
    for dirpath, dirnames, filenames in arcpy.da.Walk(workspace,
                                                      topdown=True,
                                                      datatype="RasterDataset"):                
        remove_ = []
        print(dirpath)
        for d in dirnames:
            if any(word.upper() in d.upper() for word in ignore):
                remove_.append(d)
        
        for r in remove_:
            dirnames.remove(r)        
                    
        if any(word.upper() in dirpath.upper() for word in keep_BE):    
            for filename in filenames:
                if all(word.upper() not in filename.upper() for word in ignore):
                    year = [value for key, value in yeardict.items() if dirpath.startswith(key)]
                    if not year:
                        year = ["NA"]
                    rasters_be.append([filename,os.path.join(dirpath, filename), year[0]])
                
        if any(word.upper() in dirpath.upper() for word in keep_HH):   
            for filename in filenames:
                if all(word.upper() not in filename.upper() for word in ignore):
                    year = [value for key, value in yeardict.items() if dirpath.startswith(key)]
                    if not year:
                        year = ["NA"]
                    rasters_hh.append([filename, os.path.join(dirpath, filename), year[0]])
        
        if any(word.upper() in dirpath.upper() for word in keep_VH):   
            for filename in filenames:
                if all(word.upper() not in filename.upper() for word in ignore):
                    year = [value for key, value in yeardict.items() if dirpath.startswith(key)]
                    if not year:
                        year = ["NA"]
                    rasters_vh.append([filename, os.path.join(dirpath, filename), year[0]])        

# check for duplicate names 
rasters_be = clean_names(raster_list=rasters_be, name_col=0, year_col=2)
rasters_hh = clean_names(raster_list=rasters_hh, name_col=0, year_col=2)
rasters_vh = clean_names(raster_list=rasters_vh, name_col=0, year_col=2)

print("writing to csv")
write_csv(rasters_be, csv_be)
write_csv(rasters_hh, csv_hh)
write_csv(rasters_vh, csv_vh)
print("Done")