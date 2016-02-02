"""
Build Model Inputs (Based on TTools output_to_csv v 0.92)
Ryan Michie

This script reads in the nodes feature class (built using TTools steps 1-5) and
completes the following:

1. Identifies overlapping nodes (duplicates) with a new field in
the nodes fc called DUPLICATES.

2. Builds the heat source input files and saves them in the
correct folder structure. A seperate model folder and files are
generated based on a unique group identifier.

Duplicate/Overlapping nodes can be excluded from the models

Model inputs built with this script include:
landcover data
landcover codes
morphology data
control file (from v9.0.0b14)

The remaining inputs are built by calling the heatsource
function for model setup.

The generic model startup scripts are also copied into the folders.

3. Can convert geomorph landcover codes to site potential codes.

4. Ignores stream km from the nodes fc and calculates it based on
the number of nodes in each group.


INPUTS

grouping_field = The node_fc field that will be used to organize
the nodes into seperate models

files_to_copy = files to be copied to each model folder
Tuple is like this: (copy_from, copy_to), where
0 = dir_model, 1 = dir_input

"""
# Import system modules
from __future__ import division
from __future__ import print_function
import sys
import os
import gc
import time
import arcpy
from os.path import join
from os.path import exists
from datetime import timedelta
from math import ceil
from collections import defaultdict
from operator import itemgetter
import csv
import random
import shutil

from heatsource9 import BigRedButton

# ----------------------------------------------------------------------
# Start Fill in Data

# --- Current Conditons Settings
#nodes_fc = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\TTools_Sim01_Current.gdb\Nodes_Current"
#outputdir = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Heat_Source\01_Current"
#user_txt_prefix = "Current condtion simulation for "
#sim_prefix = "sim01_current_"
#make_lccodes = True
#canopy_cover =0.35
#use_formula = False
#lccode_filename = "lccodes_current.csv"
#geomorh_to_sp_codes = False
#grouping_field = "HUC_12"
#files_to_copy = ((r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Python_Scripts\HS9_Run_Solar_Only.py",0), 
                 #(r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Python_Scripts\HS9_Setup_Model_Inputs.py", 0))
# ---

# --- Current Conditons Obs Effective Shade Obs Settings v1
nodes_fc = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\TTools_Sim01_ObsEffectiveShade.gdb\Nodes_ObsEffectiveShade_v1"
transsample_count = 15
transsample_distance = 5
lccode_filename = "lccodes_current.csv"
canopy_cover =0.85
use_formula = False

# --- Current Conditons Obs Effective Shade Obs Settings v2
#nodes_fc = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\TTools_Sim01_ObsEffectiveShade.gdb\Nodes_ObsEffectiveShade_v2"
#transsample_count = 15
#transsample_distance = 5
#lccode_filename = "lccodes_current_pow.csv"
#canopy_cover =-99
#use_formula = True

# --- Current Conditons Obs Effective Shade Obs Settings v. all
outputdir = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Heat_Source\01_Current_ObsEffectiveShade"
user_txt_prefix = "Current condtion simulation for "
sim_prefix = "sim01_current_"
make_lccodes = True
geomorh_to_sp_codes = False
grouping_field = "MODEL_GROUP"
files_to_copy = ((r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Python_Scripts\HS9_Run_Solar_Only.py",0), 
                (r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Python_Scripts\HS9_Setup_Model_Inputs.py", 0))
# ---

# --- Site Potential Settings
#nodes_fc = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\TTools_Sim02_SitePotential.gdb\Nodes_Site_Potential"
#outputdir = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Heat_Source\02_SitePotential" 
#user_txt_prefix = "Site potential simulation for "
#sim_prefix = "sim02_SitePotential_"
#make_lccodes = False
#lccode_filename = "lccodes_site_potential.csv"
#geomorh_to_sp_codes = True
#grouping_field = "HUC_12"
#files_to_copy = ((r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Python_Scripts\HS9_Run_Solar_Only.py",0), 
#                 (r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Python_Scripts\HS9_Setup_Model_Inputs.py", 0), 
#                 (r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Site_Potential\lccodes_site_potential.csv", 1))
# ---

# build model inputs excluding the overlapping nodes
remove_dup_nodes = True
update_fc_w_dups = False
cont_stream_km = True
node_dx = 200
trans_count = 8
canopy_data_type = "CanopyCover"
make_control_file = True
lcdatafile = "lcdata.csv"
morphfile = "morphdata.csv"
lccode_colnames = ["NAME", "CODE", "HEIGHT", "CANOPY_COVER", "OVERHANG"]

# This csv file contains the probability of occurrence for each vegetation 
# type within each geomorphic unit. 
# This comes from Table 1 on page C-18 in the TMDL Appendix C
input_geomorph = r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Site_Potential\geomorph_probability_table.csv"

# End Fill in Data
# ----------------------------------------------------------------------

def canopy(height_m):
    """Formula to calculate canopy cover where the power function
    passes through ht=1 and canopy=0.25 and ht=75, canopy =0.50.
    height 75 = 75th percentile of hts on the obseved nodes"""

    if height_m <=0:
        return 0
    else:
        return min([0.25*height_m**0.18262,0.55])

def nested_dict(): 
    """Build a nested dictionary"""
    return defaultdict(nested_dict)

def read_nodes_fc(nodes_fc, readfields, wherecluase):
    """Reads an input point file and returns the fields as a
    nested dictionary"""
    nodeDict = nested_dict()
    incursorFields = ["STREAM_ID","NODE_ID"] + readfields
    # Determine input point spatial units
    proj = arcpy.Describe(nodes_fc).spatialReference
            
    with arcpy.da.SearchCursor(nodes_fc, incursorFields, whereclause, proj) as Inrows:
        for row in Inrows:
            for f in xrange(0,len(readfields)):
                nodeDict[row[0]][row[1]][readfields[f]] = row[2+f]
    return(nodeDict)

def update_nodes_fc(nodes_fc, addFields, nodes_to_query, update_val):
    """Updates the input point feature class with data from the nodes dictionary"""
    
    # Build a query to retreive just the nodes that needs updating
    if len(nodes_to_query) == 0:
        whereclause = """{0} > {1}""".format("NODE_ID", -1)
    else:
        whereclause = """{0} IN ({1})""".format("NODE_ID", ','.join(str(i) for i in nodes_to_query))
    
    with arcpy.da.UpdateCursor(nodes_fc,["NODE_ID"] + addFields, whereclause) as cursor:  
        for row in cursor:
            for f, field in enumerate(addFields):
                row[f+1] = update_val
                cursor.updateRow(row)

def write_csv(outputdir, filename, colnames, outlist):
    """write the output list to csv"""
    
    # insert column header names
    outlist.insert(0, colnames)
    
    with open(join(outputdir, filename), "wb") as file_object:
        writer = csv.writer(file_object,  dialect= "excel")
        writer.writerows(outlist)        


def read_csv_dict(csvfile, key_col, val_col, skipheader=True):
    """Reads an input csv file and returns a dictionary with
    one of the columns as the dictionary keys and another as the values"""
    with open(csvfile, "rb") as f:
        reader = csv.reader(f)
        if skipheader == True: reader.next()
        csvdict = dict((row[key_col], row[val_col[0]:val_col[1]]) for row in reader)
    return csvdict

def make_sp_codes(lcdata_in, input_geomorph, trans_count, transsample_count):
    """
    This function translates geomorphic codes into site potential
    vegetation codes as described in the Willamette Basin TMDL.
    The function is based on Brian Kasper's VB macro located here:
    \\deqhq1\TMDL\Library (weekly backup)\Willamette-Basinwide\Potential Veg\
    Subbasin System Potential Veg calc.xls
    """
    # read in the geomorhic codes and vegetation probabilities
    geodict = read_csv_dict(input_geomorph, key_col=1, val_col=[2, 8], skipheader=True)
    
    # set the random seed so this is repeatable
    random.seed(42)
    
    lcdata_out = []
    
    for row in lcdata_in:
        for col in range(8, (trans_count * transsample_count) + 9):
            rnd = random.randint(1, 100) / 100
            geocode = str(int(float(row[col])))
            param = geodict[geocode]
            
            if rnd <= float(param[0]):
                spc = param[3]
            elif rnd <= float(param[0]) + float(param[1]):
                spc = param[4]
            else:
                spc = param[5]
            row[col] = int(spc)
        lcdata_out.append(row)
    
    return lcdata_out

def make_lc_codes(lcdata_in, canopy_cover, use_formula, trans_count, transsample_count):
    """
    This function reads in landcover codes from the land cover
    data file and generates the landcover code file
    based on all the unique codes.
    """
    
    codes = set()
    headerrow = True
    
    for row in lcdata_in:
        if headerrow:
            colnames = row
            headerrow = False
        else:
            for col in range(8, (trans_count * transsample_count) + 9):
                codes.add(str(int(float(row[col]))))
    
    codes = list(codes)
    codes.sort()

    if use_formula:
        lccodes = [["Current", float(code), ft2m(code[-3:]), canopy(float(code[-3:])), 0] for code in codes]
    else:   
        lccodes = [["Current", float(code), ft2m(code[-3:]), canopy_cover, 0] for code in codes]
    
    return lccodes

def ft2m(ft):
    """converts feet to meters"""
    return float(ft) * 0.3048

def setup_LC_data_headers(transsample_count, trans_count,
                          canopy_data_type, heatsource8=False):
    """Generates a list of the landcover data file
    column header names and data types"""

    type = ["LC","ELE"]
    
    #Use LAI methods   
    if canopy_data_type == "LAI":
        type = type + ["LAI","k","OH"]

    #Use Canopy Cover methods    
    if canopy_data_type == "CanopyCover":  
        type = type + ["CAN","OH"]

    lcdataheaders =[]
    # a flag indicating the model should use the heat source 8 methods 
    # (same as 8 directions but no north)
    if heatsource8 is True:
        dirs = ["T{0}".format(x) for x in range(1, 8)]
    else:        
        dirs = ["T{0}".format(x) for x in range(1, trans_count + 1)]

    zones = range(1,int(transsample_count)+1)

    # Concatenate the type, dir, and zone and order in the correct way
    for t in type:
        for d, dir in enumerate(dirs):
            for z, zone in enumerate(zones):
                if t !="ELE" and d==0 and z==0:
                    #lcdataheaders.append(t+"_EMERGENT") # add emergent
                    lcdataheaders.append(t+"_T0_S0") # add emergent
                    lcdataheaders.append("{0}_{1}_S{2}".format(t, dir, zone))
                else:
                    lcdataheaders.append("{0}_{1}_S{2}".format(t, dir, zone))

    return lcdataheaders


#enable garbage collection
gc.enable()

try:
    #keeping track of time
    startTime= time.time()
    print("Build_Model_Inputs.py")

    # Get all the column headers in the point file
    nodes_fc_headers = [field.name for field in arcpy.Describe(nodes_fc).fields]
    
    id_headers = ["STREAM_ID", "NODE_ID"]    
    lcdataheaders =["STREAM_KM","LONGITUDE","LATITUDE","TOPO_W","TOPO_S","TOPO_E"]
    morphheaders = ["STREAM_KM","ELEVATION","GRADIENT","BOTTOM_WIDTH",
                    "CHANNEL_ANGLE_Z","MANNINGS_n","SED_THERMAL_CONDUCTIVITY",
                    "SED_THERMAL_DIFFUSIVITY","SED_HYPORHEIC_THICKNESSS",
                    "%HYPORHEIC_EXCHANGE","POROSITY"]
    
    #lcsample_headers = ["LC_T","HT_T","ELE_T","LAI_T","k_T","CAN_T","OH_T"]
    lcsample_headers = setup_LC_data_headers(transsample_count, trans_count, 
                                            canopy_data_type)
    
    # This gets the landcover sample colnames by looking for 
    # them iteratively    
    for header in nodes_fc_headers:
        #if any(txt in header for txt in lcsample_headers):
        if header in lcsample_headers:
            lcdataheaders.append(header)    
    file_header_list = [lcdataheaders, morphheaders]
    file_name_list = [lcdatafile, morphfile]
    
    # find the unique values in the grouping field
    print("finding unique groups")
    with arcpy.da.SearchCursor(nodes_fc, grouping_field) as cursor:
        grouping_list = sorted(list(set([row[0] for row in cursor])))
        
    # find the nodeIDs that are overlapping. This will not work 
    # if there are three overlapping nodes
    if update_fc_w_dups:
               
        with arcpy.da.SearchCursor(nodes_fc, ["NODE_ID","LONGITUDE","LATITUDE"]) as cursor:
            latlon_list = [list(row) + [row[1]+ row[2]] for row in cursor] 
            
        del row
        
        print("Finding overlapping nodes")
        latlon_list = sorted(latlon_list, key=itemgetter(3, 1, 2, 0))
        
        dup_true = []
        dup_false = []
        
        for h, x in enumerate(latlon_list):
            if (h != 0 and
                abs(x[1] - y[1]) <= 0.00001 and
                abs(x[2] - y[2]) <= 0.00001):
                # appends nodeID
                dup_true.append(x[0])
            else:
                dup_false.append(x[0])
            y = x     
        
        del latlon_list
                    
        arcpy.AddField_management(nodes_fc, "DUPLICATE", "TEXT", "", "", "",
                                  "", "NULLABLE", "NON_REQUIRED")
        
        print("Updating nodes fc")
        #update_nodes_fc(nodes_fc, ["DUPLICATE"], [], update_val="False")
        update_nodes_fc(nodes_fc, ["DUPLICATE"], dup_false, update_val="False")
        update_nodes_fc(nodes_fc, ["DUPLICATE"], dup_true, update_val="True")
                    
        del dup_true
        del dup_false
        
        
    model_paths = []


    for group_to_query in grouping_list:
        print("Working on {0}".format(group_to_query))
        
        # make the path to the model directories
        dir_model = os.path.join(outputdir, str(group_to_query))
        dir_inputs = os.path.join(dir_model, "inputs")
        dir_outputs = os.path.join(dir_model, "outputs")
        
        model_paths.append([group_to_query, dir_model, None])
        
        # check if the output dirctories exist and create them if not
        if not os.path.exists(dir_model):
            os.makedirs(dir_model)
        if not os.path.exists(dir_inputs):
            os.makedirs(dir_inputs)
        if not os.path.exists(dir_outputs):
            os.makedirs(dir_outputs)        
        
        # Build a query to retreive just the nodes that are needed
        if remove_dup_nodes:
            whereclause = """{0} = '{1}' AND {2} = '{3}'""".format(grouping_field,
                                                                   group_to_query,
                                                                   "DUPLICATE",
                                                                   'False')
        else:
            whereclause = """{0} = '{1}'""".format(grouping_field,
                                                   group_to_query)
        
        nodeDict = read_nodes_fc(nodes_fc, nodes_fc_headers, whereclause)
        
        # reinput the stream km so it is
        # continuous over all the nodes in each group
        if cont_stream_km:
            skm = 0.0
            streamIDs = nodeDict.keys()
            streamIDs.sort()
            for streamID in streamIDs:
                nodeIDs = nodeDict[streamID].keys()
                nodeIDs.sort()
                for nodeID in nodeIDs:
                    nodeDict[streamID][nodeID]["STREAM_KM"] = skm
                    skm = round(skm + (node_dx * 0.001), 4)
    
        # Output the csv file 
        # make a wide format list by node ID from the nested dictionary
        n_nodes = 0
        for i, ouput_header_list in enumerate(file_header_list):
            outlist = []
            streamIDs = nodeDict.keys()
            streamIDs.sort()             
            for streamID in streamIDs:
                colnames = id_headers + ouput_header_list
                nodeIDs = nodeDict[streamID].keys()
                nodeIDs.sort()                 
                n_nodes = n_nodes + len(nodeIDs)
                for nodeID in nodeIDs:
                    row_list = []
                    for header in colnames:
                        if header in nodeDict[streamID][nodeID].keys():
                            val = nodeDict[streamID][nodeID][header]
                            row_list.append(val)
                        else:
                            # use None when there is no data in the 
                            # Nodes feature class
                            row_list.append(None)
                    outlist.append(row_list)

            #sort the list by stream km
            outlist = sorted(outlist, key=itemgetter(2), reverse=True)
            
            # get the correct ouput file name (lcdata or morph)
            filename = file_name_list[i]             
                                        
            # convert geomorph codes to site potential codes
            if (geomorh_to_sp_codes and filename == lcdatafile):
                outlist = make_sp_codes(outlist, input_geomorph,
                                        trans_count,
                                        transsample_count)
            
            # write it
            write_csv(dir_inputs, filename, colnames, outlist)
            
            # Make the landcover codes and output
            if (make_lccodes and filename == lcdatafile):
                lccodes = make_lc_codes(outlist, canopy_cover, use_formula, trans_count, transsample_count)
                write_csv(dir_inputs, lccode_filename, lccode_colnames, lccodes)
                del(lccodes)             
        
        if make_control_file:
            print("writing control file")
            # populate cf dictionary. format from heat source v 9.0.0b14
            cf_dict = {"usertxt": [1, "USER TEXT", user_txt_prefix + str(group_to_query)],
                       "name": [2, "SIMULATION NAME", sim_prefix + str(group_to_query)],
                       "length": [3, "STREAM LENGTH (KILOMETERS)", skm - (node_dx * 0.001)],
                       "outputdir": [4, "OUTPUT PATH", dir_outputs + "\\"],
                       "inputdir": [5, "INPUT PATH", dir_inputs + "\\"],
                       "datastart": [6, "DATA START DATE (mm/dd/yyyy)", "05/01/2014"],
                       "modelstart": [7, "MODELING START DATE (mm/dd/yyyy)", "08/1/2014"],
                       "modelend": [8, "MODELING END DATE (mm/dd/yyyy)", "08/1/2014"],
                       "dataend": [9, "DATA END DATE (mm/dd/yyyy)", "10/30/2014"],
                       "flushdays": [10, "FLUSH INITIAL CONDITION (DAYS)", 1],
                       "offset": [11, "TIME OFFSET FROM UTC (HOURS)", -7],
                       "dt": [12, "MODEL TIME STEP - DT (MIN)", 1],
                       "dx": [13, "MODEL DISTANCE STEP - DX (METERS)", node_dx],
                       "longsample": [14, "LONGITUDINAL STREAM SAMPLE DISTANCE (METERS)", node_dx],
                       "bcfile": [15, "BOUNDARY CONDITION FILE NAME", "boundary_conditions.csv"],
                       "inflowsites": [16, "TRIBUTARY SITES", 0],
                       "inflowinfiles": [17, "TRIBUTARY INPUT FILE NAMES", "tribs.csv"],
                       "inflowkm": [18, "TRIBUTARY MODEL KM", None],
                       "accretionfile": [19, "ACCRETION INPUT FILE NAME", "accretion_inputs.csv"],
                       "climatesites": [20, "CLIMATE DATA SITES", 1],
                       "climatefiles": [21, "CLIMATE INPUT FILE NAMES", "climate.csv"],
                       "climatekm": [22, "CLIMATE MODEL KM", 1],
                       "calcevap": [23, "INCLUDE EVAPORATION LOSSES FROM FLOW (TRUE/FALSE)", "FALSE"],
                       "evapmethod": [24, "EVAPORATION METHOD (Mass Transfer/Penman)", "Mass Transfer"],
                       "wind_a": [25, "WIND FUNCTION COEFFICIENT A", 0.00000000151],
                       "wind_b": [26, "WIND FUNCTION COEFFICIENT B", 0.0000000016],
                       "calcalluvium": [27, "INCLUDE DEEP ALLUVIUM TEMPERATURE (TRUE/FALSE)", "FALSE"],
                       "alluviumtemp": [28, "DEEP ALLUVIUM TEMPERATURE (*C)", None],
                       "morphfile": [29, "MORPHOLOGY DATA FILE NAME", morphfile],
                       "lcdatafile": [30, "LANDCOVER DATA FILE NAME", lcdatafile],
                       "lccodefile": [31, "LANDCOVER CODES FILE NAME", lccode_filename],
                       "trans_count": [32, "NUMBER OF TRANSECTS PER NODE", trans_count],
                       "transsample_count": [33, "NUMBER OF SAMPLES PER TRANSECT", transsample_count],
                       "transsample_distance": [34, "DISTANCE BETWEEN TRANSESCT SAMPLES (METERS)", transsample_distance],
                       "emergent": [35, "ACCOUNT FOR EMERGENT VEG SHADING (TRUE/FALSE)", "FALSE"],
                       "lcdatainput": [36, "LANDCOVER DATA INPUT TYPE (Codes/Values)", "Codes"],
                       "canopy_data": [37, "CANOPY DATA TYPE (LAI/CanopyCover)", canopy_data_type],
                       "vegDistMethod": [38, "VEGETATION ANGLE CALCULATION METHOD (point/zone)", "point"],
                       "heatsource8": [39, "USE HEAT SOURCE 8 LANDCOVER METHODS (TRUE/FALSE)", "FALSE"]}            
            
            # sort so we have a list in the order of the line number
            cf_sorted = sorted(cf_dict.items(), key=itemgetter(1))
            cf_list = [line[1] for line in cf_sorted]
        
            cf_header = ["LINE", "PARAMETER", "VALUE"]
            write_csv(dir_model, "HeatSource_Control.csv",
                      cf_header, cf_list)
        
        # Build the other input files
        BigRedButton.run_input_setup(dir_model,"HeatSource_Control.csv",
                                     use_timestamp=False,
                                     overwrite=False)
            
        # copy the files to the model directory folder
        for copy_from, copy_to in files_to_copy:
            if copy_to == 0:
                shutil.copy(copy_from, dir_model)
            elif copy_to == 1:
                shutil.copy(copy_from, dir_inputs)
            else:
                shutil.copy(copy_from, copy_to)
        
        del nodeDict
        
    write_csv(outputdir, "model_directory.csv", ["GROUP", "PATH", "STATUS"], model_paths)

    endTime = time.time()
    gc.collect()
    
    elapsedmin= ceil(((endTime - startTime) / 60)* 10)/10
    mspernode = timedelta(seconds=(endTime - startTime) / n_nodes / 2).microseconds
    print("Process Complete in %s minutes. %s microseconds per node" % (elapsedmin, mspernode))    

# For arctool errors
except arcpy.ExecuteError:
    msgs = arcpy.GetMessages(2)
    #arcpy.AddError(msgs)
    print(msgs)

# For other errors
except:
    import traceback, sys
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]

    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

    #arcpy.AddError(pymsg)
    #arcpy.AddError(msgs)

    print(pymsg)
    print(msgs)	
