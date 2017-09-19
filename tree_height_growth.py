from __future__ import division
from math import exp
from math import log

"""
This module contains a collection of functions to calculate
a mean tree height in meters using various height growth curves found
in the literature.

5/04/2016
Ryan Michie
Oregon DEQ

# ---------------
Citations

Bruce D. 1981. Consistent height-growth and growth-rate estimates for 
remeasured plots. Forest Science 27(4):711-725.

Curtis, R.O., Herman, F.R., DeMars, D.J. 1974. Height growth and site
index for Douglas-fir in high-elevation forests of the Oregon-Washington
Cascades. Forest Science 20(4):307-316.

Farr, W.A. 1984. Site index and height growth curves for unmanaged
even-aged stands of Western hemlock and Sitka spruce in southeast Alaska.
Research Paper. PNW-326. U.S. Department of Agriculture, Forest Service,
Pacific Northwest Forest and Range Experiment Station. Portland, OR.

Keyser, C.E. 2008a (revised June 16, 2015). Pacific northwest coast (PN)
variant overview forest vegetation simulator. Internal Report Fort
Collins, CO: U.S. Department of Agriculture, Forest Service,
Forest Management Service Center.

Keyser, C.E. 2008b (revised June 16, 2015). Westside cascades (WC)
variant overview forest vegetation simulator. Internal Report.
Fort Collins, CO: U.S. Department of Agriculture, Forest Service,
Forest Management Service Center.

King, J.E. 1966. Site index curves for Douglas-fir in the pacific
northwest. Weyerhaeuser Forestry Paper No. 8. Weyerhaeuser Forestry
Research Center. Centralia, WA. 

Kurucz, J.F. 1985 Metric SI tables for red cedar stands.
In: Mitchell K.J., Polsson, K.R. 1988. Site index curves and tables for
British Columbia: Coastal Species. Report 37. Forest Resource
Development Agreement, BC Ministry of Forests and Lands,
Government of Canada

Mitchell K.J., Polsson, K.R. 1988. Site index curves and tables for
British Columbia: Coastal Species. Report 37. Forest Resource
Development Agreement, BC Ministry of Forests and Lands,
Government of Canada.

Thrower J.S., Goudie, J.W. 1992. Development of height-age and
site-index fuctions for even age interior douglas-fir in British
Columbia. Research Note No. 109. BC Ministiry of Forests and Lands,
Government of Canada

Worthington N.P., Johnson F.A., Staebler G.R., Lloyd W.J. 1960, Normal
yield tables for red alder. Research Paper 36. U.S. Department of
Agricuture, Forest Service, Pacfifc Northwest Forest and Range
Experiment Station, Portland, OR.
"""


def ht_western_redcedar_farr(si50_ft, tree_age, ytobh=4.7):
    """
    Returns height in meters of western redcedar given the
    50 year base site index height in feet, tree age, and
    years to breast height. Equation is from Farr 1984 using
    formulation presented in Keyser 2008a. Keyser 2008a uses
    this equation in the Forest Vegetation Simulator (FVS)
    Pacific Northwest Coast (PN) variant to calcuate
    height of Western redcedar and Sitka spruce.
    Defulat of 4.7 years required to reach
    breast height from Harrington and Gould 2010 "Growth of Western
    Redcedar and Yellow-Cedar" page 99 in PNW-GTR-828
    (A Tale of Two Cedars...)
    """
    
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

def ht_western_redcedar_kurucz(si50_m, tree_age, ytobh=4.7):
    """
    Returns height in meters of western redcedar given the
    50 year base site index height in meters, tree age,
    and the years to breast height. Equation is
    from Mitchell and Polsson 1988 using formulation
    presented in Kurucz 1985. Defulat of 4.7 years required to reach
    breast height from Harrington and Gould 2010 "Growth of Western
    Redcedar and Yellow-Cedar" page 99 in PNW-GTR-828
    (A Tale of Two Cedars...)
    """
    age_bh = tree_age - ytohb
    
    # height equation from Mitchell and Polsson 1988 - pg 7 (appendix 2)
    # height is in meters
    b1 = -3.11785 + (0.05027 * 2500) / (si50_m - 1.3)
    b2 = -0.02465 + (0.01411 * 2500) / (si50_m - 1.3)
    b3 = 0.00174 + (0.000097667 * 2500) / (si50_m - 1.3)
    ht_m = 1.3 + (age_bh * age_bh) / (b1 + (b2 * age_bh) + (b3 * (age_bh * age_bh)))
    if age_bh > 50:
        ht_m = ht_m + 0.02379545 * ht_m - 0.000475909 * age_bh * ht_m
    
    return ht_m

def ht_douglas_fir_king(si50_ft, tree_age, ytobh):
    """
    Returns height in meters of Douglas fir given the 50 year base
    site index height in feet, tree age, and years to breast height.
    Equation is from King 1966.
    """     
        
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

def ht_douglas_fir_curtis(si100_ft, tree_age):
    """
    Returns height in meters of Douglas fir given the
    100 year base site index height in feet and tree age.
    Equation is from Curtis et al 1974.
    """    
    
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

def ht_douglas_fir_bruce(si50_ft, tree_age, ytobh):
    """
    Returns height in meters of Douglas fir given the
    50 year base site index height in feet, tree age, and
    years to breast height.
    Equations are from Bruce (1981).
    """    
    
    b3 = -0.477762 - 0.894427 * (si50_ft / 100) + 0.793548 * ((si50_ft / 100)** 3)
    b2 = log(4.5/si50_ft) / ((ytobh ** b3) - (63.25 - si50_ft / 20) ** b3)
    
    ht_ft = (si50_ft * exp(b2*((tree_age) **b3 - (63.25 - si50_ft / 20) ** b3)))
    ht_m = ht_ft * 0.3048
    
    return ht_m

def ht_other(si100_ft, tree_age, ytobh, adj):
    """
    Returns the height of a tree without a specfic site index curve.
    The equation is based on the 100 year base site index height
    of Douglas Fir in feet from Curtis et al 1974.
    Keyser 2008a and Keyser 2008b use this equation in
    the Forest Vegetation Simulator (FVS) to calcuate height
    of other species given an adjustment factor to site index.
    Adjustment factors for each species is found in table 3.4.2. This
    equation can be used for Alaska cedar / western larch, Douglas-fir,
    coast redwood, western redcedar, bigleaf maple,
    white alder / Pacific madrone, paper birch, giant chinquapin /
    tanoak, quaking aspen, black cottonwood, western juniper,
    whitebark pine, knobcone pine, Pacific yew, Pacific dogwood,
    hawthorn species, bitter cherry,
    willow species, and others
    """    
    
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

def ht_red_alder_worthington(si50_ft, tree_age):
    """
    Returns the height of red alder in meters given the
    50 year base site index height in feet and tree age.
    Equations are from Worthington et al 1960.
    """
    
    b0 = 0.60924
    b1 = 19.538
    
    ht_m = 1 / ((b0 + b1 / tree_age) / si50_ft) * 0.3048
    
    return ht_m

def ytobh_bruce(si50_ft):
    """
    Returns the years required to reach breast height
    from equation 8 in Bruce (1981). Applies to Douglas Fir.
    """
    ytobh = 13.25 - si50_ft / 20
    
    return ytobh

def ytohh_harrington():
    """
    4.7 years required to reach
    breast height from Harrington and Gould 2010 "Growth of Western
    Redcedar and Yellow-Cedar" page 99 in PNW-GTR-828
    (A Tale of Two Cedars...)
   """
    return 4.7

def ytobh_thrower(si50_ft, yrst=4):
    """
    Returns the years required to reach breast height
    from equation 10 in Thrower and Goudie (1992).
    yrst = year to stump height  (0.3 m) 
    Authors used average of 4 years for yrst.
    Can be different based on SI.
    """
    ytobh = yrst + (98.97 * 1 / si50_ft)
    
    return ytobh

def ytobh_mitchell():
    """
    Mitchell and Polsson 1988 calcualte a mean of 9.5 years to
    reach breast height for Western Redcedar.
    """
    return 9.5
    
    