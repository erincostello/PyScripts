
"""
This script generates the site potential landcover codes and year based
height growth from the treatment type, height growth
curves, treatment complete year (planting year), model year, 
and other information from the imported heat source landcover
code data file. The script outputs a new heat source landcover code
data files for each model year and the generic site potenial
found in the TMDL.

7/17/2015
Ryan Michie
Oregon DEQ
"""
from __future__ import division, print_function
from math import exp
from math import log
from collections import defaultdict
from os.path import join
import csv
import imp

# list of the model years
model_years = [2020, 2025, 2030, 2035, 2040]

# inputs and outputs are located in this directory
dirpath =r"C:\WorkSpace\Quantifying_Conservation_2014\SouthernWillamette\Landcover_Codes"

# This file acts as a lookup table to determine 
# how to apply the growth equations based on the input code
# The file should be located in the 'dirpath' from above
lccode16_dict_csv = "landcover_codes_dict.csv"

# Name of the input lccodes csv that has the 
# current condtion landcover code values
lccode_current = "lccodes_treatments_current.csv"

# This is the name of the output lccode csv file. 
# The year will be appended to this name when the file is output
lccode_data_csv = "lccodes_treatments"

# This is for site potential independent of year
lccode_data_sp_csv = "lccodes_treatments_sp"

# This is an alternative method.
# Instead of reading in an existing lccodes csv
# I build a single set codes that cover all the possible values
#---------------------------------------------------------
# This is the 16bit codes without height
#site = [i for i in range(11000, 46000, 1000)]

# This is the height range in meters
#ht = [i for i in range(0, 400)]

# Put it all togehter
#lccodes = [s + h for s in site for h in ht]
#---------------------------------------------------------

def str2bool(val):
    """Converts a 'True' string to the cooresponding
    python boolean True value. If the string has any other values,
    False will be returned."""
    return val.lower() in ("true")

def read_csv_to_list(inputdir, filename, skipheader=True):
    """Reads an input csv file and returns a a list"""
    with open(join(inputdir, filename.strip()), "rb") as f:
        reader = csv.reader(f)
        if skipheader == True: reader.next()
        csvlist = [row for row in reader]
    return csvlist

def read_csv_to_dict(inputdir, filename):
    """Reads data into a dictionary and uses the
    first colunm (landcover code) as the key. The dictionary value list looks
    like this: [TreatmentSite, CompleteYear, Treatment LUID, SI_Region]
    """
    data=defaultdict(list)  # each value in each column is appended to a list
    with open(join(inputdir, filename.strip()), "rU") as file_object:
        reader = csv.reader(file_object, dialect="excel")
        reader.next()  # skip the header row
        mydict = {int(row[0]): [str2bool(row[1]), int(row[2]), int(row[3]), row[4]] for row in reader}
    return mydict

def write_csv(outputdir, filename, colnames, outlist):
    """write the output list to csv"""
    
    # insert column header names
    outlist.insert(0, colnames)
    
    with open(join(outputdir, filename), "wb") as file_object:
        writer = csv.writer(file_object,  dialect= "excel")
        writer.writerows(outlist)

# Read in the lookup table to know how to use each code
lccode16_dict = read_csv_to_dict(dirpath, lccode16_dict_csv)

lccodes_list = read_csv_to_list(dirpath, lccode_current)

# Apply Site Potential based on treatment type
# see page C-33 of the TMDL Appendix A.
# http://www.deq.state.or.us/WQ/TMDLs/docs/willamettebasin/willamette/appxctemp.pdf

lccodes_new = []

for row in lccodes_list:
    lccode = row[1]
    ht_current = float(row[2])  # this is in meters
    
    if lccode != '-9999.0':
        raw_code = int(str(lccode)[:2])
        print(lccode, raw_code, ht_current)
        
        # values should look something like this:
        # True, 2000, 80, pn
        treatment_site, complete_year, treatment_luid, variant = lccode16_dict[raw_code]
        
        if treatment_site:
            
            # Treatment LUID
            if treatment_luid == 80:
                # 80 Conifer
                treatment = "Conifer"
                treatment_avg_ht = 160 * 0.3048
                canopy_cover = 0.75
                overhang = 4.9
                
            elif treatment_luid == 81: 
                # 81 Conifer and Hardwood
                treatment = "Conifer and Hardwood"
                treatment_avg_ht = 90 * 0.3048
                canopy_cover = 0.75
                overhang = 3.3
            
            elif treatment_luid == 82:
                # 82 Hardwood
                treatment = "Hardwood"
                treatment_avg_ht = 67 * 0.3048
                canopy_cover = 0.75
                overhang = 3.1
                
            ht_new = int(treatment_avg_ht + 0.5)
            
            if ht_current > ht_new:
                desc = "{0} Treatment Site Existing Vegetation".format(treatment)
                ht_new = ht_current
                canopy_cover = 0.85
                overhang = 0
                
            else:
                desc = "{0} Treatment Site Plantings".format(treatment)
                
                
            row[0] = desc
            row[2] = ht_new
            row[3] = canopy_cover
            row[4] = overhang            
            
        else:
            desc = "Non-Treatment Site"
            
            row[0] = desc
                    
    lccodes_new.append(row)
            
lccodesheader = ["NAME","CODE","HEIGHT", "CANOPY_COVER","OVERHANG"]
outfilename = "{0}.csv".format(lccode_data_sp_csv)
write_csv(dirpath, outfilename, lccodesheader, lccodes_new)

# Using the same values as current conditions
canopy_cover = 0.85
overhang = 0

for model_year in model_years:
    
    lccodes_new = []

    for row in lccodes_list:
        lccode = row[1]
        ht_current = float(row[2]) # in meters
        
        if lccode != '-9999.0':
            raw_code = int(str(lccode)[:2])
            print(lccode, raw_code, ht_current)
            
            # values should look something like this:
            # True, 2000, 80, pn
            treatment_site, complete_year, treatment_luid, variant = lccode16_dict[raw_code]
            
            if treatment_site:
                
                tree_age = model_year - complete_year
            
                if variant == 'wc':
                    print(duh)
                    # Westside Cascades Variant
                    redcedar = tree.ht_western_redcedar_kurucz(si50_m=35, tree_age=tree_age)
                    doug_fir = tree.ht_douglas_fir_curtis(si100_ft=111, tree_age=tree_age)
                    
                    redalder = tree.ht_red_alder_worthington(si50_ft=90, tree_age=tree_age)
                    
                    # Site index and adjustment factors for each species below 
                    # is based on in Keyser 2008b (see table 3.4.2) 
                    dogwood = tree.ht_other(si100_ft=73, tree_age=tree_age, ytobh=1, adj=.60)
                    or_ash = tree.ht_other(si100_ft=73, tree_age=tree_age, ytobh=1, adj=.50)
                    willow = tree.ht_other(si100_ft=73, tree_age=tree_age, ytobh=1, adj=.50)
                    cottonwood = tree.ht_other(si100_ft=73, tree_age=tree_age, ytobh=1, adj=.85)
                    bl_maple = tree.ht_other(si100_ft=73, tree_age=tree_age, ytobh=1, adj=.75)
                    
                
                elif variant == 'pn':
                    # Pacfic Northwest Coast Variant
                    redcedar = tree.ht_western_redcedar_farr(si50_ft=115,
                                                             tree_age=tree_age)
                    doug_fir = tree.ht_douglas_fir_bruce(si50_ft=90,
                                                         tree_age=tree_age,
                                                         ytobh=tree.ytobh_bruce())
                    
                    redalder = tree.ht_red_alder_worthington(si50_ft=90,
                                                             tree_age=tree_age)
                    
                    # Site index and adjustment factors for each species below 
                    # is based on in Keyser 2008a (see table 3.4.2)               
                    dogwood = tree.ht_other(si100_ft=98, tree_age=tree_age, ytobh=1, adj=.60)
                    or_ash = tree.ht_other(si100_ft=98, tree_age=tree_age, ytobh=1, adj=.50)
                    willow = tree.ht_other(si100_ft=98, tree_age=tree_age, ytobh=1, adj=.50)
                    cottonwood = tree.ht_other(si100_ft=98,tree_age=tree_age, ytobh=1, adj=.85)
                    bl_maple = tree.ht_other( si100_ft=98, tree_age=tree_age, ytobh=1, adj=.75)
                
                # Treatment LUID
                if treatment_luid == 80:
                    # 80 Conifer
                    treatment = "Conifer"
                    treatment_avg_ht = (redcedar * 0.54) + (doug_fir * 0.46)
                    
                elif treatment_luid == 81: 
                    # 81 Conifer and Hardwood
                    treatment = "Conifer and Hardwood"
                    treatment_avg_ht = ((0.50 * ((dogwood * 0.33) +
                                                 (willow * 0.24) +
                                                 (or_ash * 0.15) +
                                                 (cottonwood * 0.09) +
                                                 (redalder * 0.08) +
                                                 (bl_maple * 0.07))) +
                                        (0.50 * ((redcedar * 0.54) +
                                                 (doug_fir * 0.46))))
                
                elif treatment_luid == 82:
                    # 82 Hardwood
                    treatment = "Hardwood"
                    treatment_avg_ht = ((dogwood * 0.33) +
                                        (willow * 0.24) +
                                        (or_ash * 0.15) +
                                        (cottonwood * 0.09) +
                                        (redalder * 0.08) +
                                        (bl_maple * 0.07))
                    
                ht_new = int(treatment_avg_ht + 0.5)
                
                if ht_current > 8 and ht_current > ht_new:
                    desc = "{0} Treatment Site Existing Vegetation".format(treatment)
                    ht_new = ht_current
                    
                else:
                    desc = "{0} Treatment Site Plantings - Age {1}".format(treatment, tree_age)
                    
                    
                row[0] = desc
                row[2] = ht_new
                row[3] = canopy_cover
                row[4] = overhang

            else:
                desc = "Non-Treatment Site"
                
                row[0] = desc
            
        lccodes_new.append(row)
    
    lccodesheader = ["NAME","CODE","HEIGHT", "CANOPY_COVER","OVERHANG"]
    outfilename = "{0}_{1}.csv".format(lccode_data_csv, model_year)
    write_csv(dirpath, outfilename, lccodesheader, lccodes_new)

print("done")


