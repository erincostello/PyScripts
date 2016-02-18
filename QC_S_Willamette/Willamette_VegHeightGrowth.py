
"""
This script calculates a mean treatment height using height growth
curves, treatment complete year (planting year), model year 
and other information from the imported heat source landcover
code data file. The script outputs a new heat source landcover code
data file for each model year.

7/17/2015
Ryan Michie
Oregon DEQ

# ---------------
Citations

Bruce D. 1981. Consistent height-growth and growth-rate estimates for 
remeasured plots. Forest Science 27(4):711-725.

Curtis, R.O., Herman, F.R., DeMars, D.J. 1974. Height growth and site index for
Douglas-fir in high-elevation forests of the Oregon-Washington Cascades. Forest Science 20(4):307-316.

Farr, W.A. 1984. Site index and height growth curves for unmanaged even-aged stands of
Western hemlock and Sitka spruce in southeast Alaska. Research Paper. PNW-326.
U.S. Department of Agriculture, Forest Service, Pacific Northwest Forest and Range Experiment Station. Portland, OR.

Keyser, C.E. 2008a (revised June 16, 2015). Pacific northwest coast (PN) variant overview
forest vegetation simulator. Internal Report Fort Collins, CO: U.S. Department of Agriculture, Forest
Service, Forest Management Service Center.

Keyser, C.E. 2008b (revised June 16, 2015). Westside cascades (WC) variant overview
forest vegetation simulator. Internal Report. Fort Collins, CO: U.S. Department of Agriculture, Forest
Service, Forest Management Service Center.

King, J.E. 1966. Site index curves for Douglas-fir in the pacific northwest. Weyerhaeuser
Forestry Paper No. 8. Weyerhaeuser Forestry Research Center. Centralia, WA. 

Kurucz, J.F. 1985 Metric SI tables for red cedar stands. In: Mitchell K.J., Polsson, K.R. 1988. Site index curves and tables for British Columbia: Coastal Species. 
Report 37. Forest Resource Development Agreement, BC Ministry of Forests and Lands, Government of Canada

Mitchell K.J., Polsson, K.R. 1988. Site index curves and tables for British Columbia: Coastal Species. Report 37. 
Forest Resource Development Agreement, BC Ministry of Forests and Lands, Government of Canada.

Worthington N.P., Johnson F.A., Staebler G.R., Lloyd W.J. 1960, Normal yield tables for red alder. Research Paper 36.
U.S. Department of Agricuture, Forest Service, Pacfifc Northwest Forest and Range Experiment Station, Portland, OR.
"""

from __future__ import division, print_function
from math import exp
from math import log
from collections import defaultdict
from os.path import join
import csv

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

# Using the same values as current conditions
canopy_cover = 0.85
overhang = 0

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


def ht_western_redcedar_farr(tree_age, si50_ft):
    """Calculate the height of western redcedar in meters given the
    tree age and the 50 year base site index height in feet. Equation is
    from Farr 1984 using formulation presented in Keyser 2008a.
    Keyser 2008a uses this equation in the Forest Vegetation
    Simulator (FVS) Pacific Northwest Coast (PN) variant to calcuate
    height of Western redcedar and Sitka spruce."""
    
    b0 = -0.2050542
    b1 = 1.449615
    b2 = -0.01780992
    b3 = 0.0000651975
    b4 = -0.0000000000000000000000109559
    b5 = -5.611879
    b6 = 2.418604
    b7 = -0.259311
    b8 = 0.000135145
    b9 = -0.00000000000170114
    b10 = 0.0000000000000000000000000079642
    b11 = -86.43
    
    # calculate the years required to reach breast height 
    # from equation 8 in Bruce (1981).
    ytobh = 13.25 - si50_ft / 20
        
    # calculate the breast height age
    age_bh = tree_age - ytobh     
    
    ht_ft = (4.5 +
             exp(b0 + b1* log(age_bh) +
                 b2*(log(age_bh))**3 +
                 b3*(log(age_bh))**5 +
                 b4*(log(age_bh))**30) +
             ((si50_ft - 4.5) +
              b11) *
             (exp (b5 + b6* log(age_bh) +
                   b7 * (log(age_bh))**2 +
                   b8*(log(age_bh))**5 +
                   b9*(log(age_bh))**16 +
                   b10* (log(age_bh))**36)
              )
             )
    
    ht_m = ht_ft * 0.3048
    
    return ht_m    

def ht_western_redcedar_kurucz(tree_age, si50_m):
    """Calculate the height of western redcedar given the tree age and
    the 50 year base site index height in meters. Equation is
    from Mitchell and Polsson 1988 using formulation
    presented in Kurucz 1985."""
    
    # mean years required to reach breast height from 
    # Harrington and Gould 2010 "Growth of Western Redcedar 
    # and Yellow-Cedar" page 99 in PNW-GTR-828 (A Tale of Two Cedars...)
    # Note Mitchell and Polsson 1988 calcualte a mean of 9.5 years.
    age_bh = tree_age - 4.7
    
    # height equation from Mitchell and Polsson 1988 - pg 7 (appendix 2)
    # height is in meters
    b1 = -3.11785 + (0.05027 * 2500) / (si50_m - 1.3)
    b2 = -0.02465 + (0.01411 * 2500) / (si50_m - 1.3)
    b3 = 0.00174 + (0.000097667 * 2500) / (si50_m - 1.3)
    ht_m = 1.3 + (age_bh * age_bh) / (b1 + (b2 * age_bh) + (b3 * (age_bh * age_bh)))
    if age_bh > 50:
        ht_m = ht_m + 0.02379545 * ht_m - 0.000475909 * age_bh * ht_m
    
    return ht_m

def ht_douglas_fir_king(tree_age, si50_ft):
    """Calculates the height of Douglas fir given tree age and
        the 50 year base site index height in feet. Equation is from 
        King 1966."""     
    
    # calculate the years required to reach breast height 
    # from equation 8 in Bruce (1981).
    ytobh = 13.25 - si50_ft / 20
        
    # calculate the breast height age
    age_bh = tree_age - ytobh    
    
    b0	= -0.954038
    b1	= 0.109757
    b2	= 0.0558178
    b3	= 0.00792236
    b4	= -0.000733819
    b5	= 0.000197693
    Z = 2500 / (si50_ft - 4.5)
    
    ht_ft = (((age_bh**2) / (b0 + (b1 * Z) + ((b2 + (b3 * Z)) * age_bh) + ((b4 + (b5 * Z)) * age_bh**2))) + 4.5)
    
    ht_m = ht_ft * 0.3048
    
    return ht_m

def ht_douglas_fir_curtis(tree_age, si100_ft):
    """Calculates the height of Douglas fir given tree age and
    the 100 year base site index height in feet. Equation is from 
    Curtis et al 1974."""    
    
    b0 = 0.6192
    b1 = -5.3394
    b2 = 240.29
    b3 = 3368.9
    
    ytobh = 0
    
    # calculate the breast height age
    age_bh = tree_age - ytobh      
    
    ht_ft = (((si100_ft - 4.5) /
             (b0 + (b1 / (si100_ft  - 4.5))) + (b2 + (b3 / (si100_ft  - 4.5))) *
              age_bh**-1.4) + 4.5)  
    
    ht_m = ht_ft * 0.3048
         
    return ht_m

def ht_douglas_fir_bruce(tree_age, si50_ft):
    """Calculates the height of Douglas fir in meters given tree age and
    the 50 year base site index height in feet. Equations are from 
    Bruce (1981)."""    
    
    # calculate the years required to reach breast height 
    # from equation 8 in Bruce (1981)
    ytobh = 13.25 - si50_ft / 20
    
    b3 = -0.477762 - 0.894427 * (si50_ft / 100) + 0.793548 * ((si50_ft / 100)** 3)
    b2 = log(4.5/si50_ft) / ((ytobh ** b3) - (63.25 - si50_ft / 20) ** b3)
    
    ht_ft = (si50_ft * exp(b2*((tree_age) **b3 - (63.25 - si50_ft / 20) ** b3)))
    ht_m = ht_ft * 0.3048
    
    return ht_m

def ht_other(tree_age, si100_ft, ytobh, adj):
    """Calculates the height of a tree without a specfic site index curve.
    The equation is based on the 100 year base site index height
    of Douglas Fir in feet from Curtis et al 1974.
    Keyser 2008a and Keyser 2008b use this equation in
    the Forest Vegetation Simulator (FVS) to calcuate height
    of other species given an adjustment factor to site index.
    Adjustment factors for each species is found in table 3.4.2. This equation can be used for
    Alaska cedar / western larch, Douglas-fir, coast redwood,
    western redcedar, bigleaf maple, white alder / Pacific madrone,
    paper birch, giant chinquapin / tanoak, quaking aspen,
    black cottonwood, western juniper, whitebark pine, knobcone pine,
    Pacific yew, Pacific dogwood, hawthorn species, bitter cherry,
    willow species, and others"""    
    
    b0 = 0.6192
    b1 = -5.3394
    b2 = 240.29
    b3 = 3368.9
    
    # calculate the breast height age
    age_bh = tree_age - ytobh      
    
    # Apply adjustment to site index from Keyser 2008
    si_adj = si100_ft * adj 
    
    ht_ft = (((si_adj - 4.5) /
             (b0 + (b1 / (si_adj - 4.5))) + (b2 + (b3 / (si_adj - 4.5))) *
              age_bh**-1.4) + 4.5)  
    
    ht_m = ht_ft * 0.3048
         
    return ht_m

def ht_red_alder_worthington(tree_age, si50_ft):
    """Calculate the height of red alder in meters given the tree age and
        the 50 year base site index height in feet. Equations are
        from Worthington et al 1960."""
    
    b0 = 0.60924
    b1 = 19.538
    
    ht_m = 1 / ((b0 + b1 / tree_age) / si50_ft) * 0.3048
    
    return ht_m

# Read in the lookup table to know how to use each code
lccode16_dict = read_csv_to_dict(dirpath, lccode16_dict_csv)


lccodes_list = read_csv_to_list(dirpath, lccode_current)

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


for model_year in model_years:
    
    lccodes_new = []

    for row in lccodes_list:
        lccode = row[1]
        ht_current = float(row[2])
        
        if lccode != '-9999.0':
            raw_code = int(str(lccode)[:2])
            print(lccode, raw_code, ht_current)
            
            # values should look something like this:
            # True, 2000, 80, pn
            treatment_site, complete_year, treatment_luid, variant = lccode16_dict[raw_code]
            
            if treatment_site:
                
                tree_age = model_year - complete_year
            
                if variant == 'wc':
                    # Westside Cascades Variant
                    redcedar = ht_western_redcedar_kurucz(tree_age, si50_m=35)
                    doug_fir = ht_douglas_fir_curtis(tree_age, si100_ft=111)
                    
                    redalder = ht_red_alder_worthington(tree_age, si50_ft=90)
                    
                    # Site index and adjustment factors for each species below 
                    # is based on in Keyser 2008b (see table 3.4.2) 
                    dogwood = ht_other(tree_age, si100_ft=73, ytobh=1, adj=.60)
                    or_ash = ht_other(tree_age, si100_ft=73, ytobh=1, adj=.50)
                    willow = ht_other(tree_age, si100_ft=73, ytobh=1, adj=.50)
                    cottonwood = ht_other(tree_age, si100_ft=73, ytobh=1, adj=.85)
                    bl_maple = ht_other(tree_age, si100_ft=73, ytobh=1, adj=.75)
                
                elif variant == 'pn':
                    # Pacfic Northwest Coast Variant
                    redcedar = ht_western_redcedar_farr(tree_age, si50_ft=115)
                    doug_fir = ht_douglas_fir_bruce(tree_age, si50_ft=90)
                    
                    redalder = ht_red_alder_worthington(tree_age, si50_ft=90)
                    
                    # Site index and adjustment factors for each species below 
                    # is based on in Keyser 2008a (see table 3.4.2)               
                    dogwood = ht_other(tree_age, si100_ft=98, ytobh=1, adj=.60)
                    or_ash = ht_other(tree_age, si100_ft=98, ytobh=1, adj=.50)
                    willow = ht_other(tree_age, si100_ft=98, ytobh=1, adj=.50)
                    cottonwood = ht_other(tree_age, si100_ft=98, ytobh=1, adj=.85)
                    bl_maple = ht_other(tree_age, si100_ft=98, ytobh=1, adj=.75)
                
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


