from __future__ import division, print_function
from math import exp

def ht_western_redcedar(tree_age, site_index_50_m):
    """Calculate the height of western redcedar given the tree age and
    the 50 year base site index height in meters. Equation is
    from Mitchell and Polsson 1988 using formulation of Kurucz 1985."""
    
    # calculate the years required to reach breast height (cited from King 1966) 
    ytobh = 13.25 - site_index_50_m / 6.069
    
    # calculate the breast height age
    age_bh = tree_age - ytobh
    
    # height equation from Mitchell and Polsson 1988 - pg 7 (appendix 2)
    # height is in meters
    b1 = -3.11785 + (0.05027 * 2500) / (site_index_50_m - 1.3)
    b2 = -0.02465 + (0.01411 * 2500) / (site_index_50_m - 1.3)
    b3 = 0.00174 + (0.000097667 * 2500) / (site_index_50_m - 1.3)
    ht = 1.3 + (age_bh * age_bh) / (b1 + (b2 * age_bh) + (b3 * (age_bh * age_bh)))
    if age_bh > 50:
        ht = ht + 0.02379545 * ht - 0.000475909 * age_bh * ht
    
    return ht

def ht_douglas_fir(tree_age, site_index_100_ft, adj):
    """Calculates the height of Douglas fir given tree age and
    the 100 year base site index height in feet. Equation is from 
    Curtis et al 1974.  Keyser 2008 (revised Novemeber 2014) uses
    this equation in the Forest Vegetation Simulator to calcuate height
    of other species given an adjustment to site index. Can be used for
    species Alaska cedar / western larch, Douglas-fir, coast redwood,
    western redcedar, bigleaf maple, white alder / Pacific madrone,
    paper birch, giant chinquapin / tanoak, quaking aspen,
    black cottonwood, western juniper, whitebark pine, knobcone pine,
    Pacific yew, Pacific dogwood, hawthorn species, bitter cherry,
    willow species, other species"""    
    
    b0 = 0.6192
    b1 = -5.3394
    b2 = 240.29
    b3 = 3368.9
    
    # If not for Douglas fir use adjustment from Keyser 2008
    si_adj = site_index_100_ft * adj 
    
    ht_ft = ((si_adj - 4.5) /
          (b0 + (b1 / (si_adj - 4.5)) + (b2 + (b3 / (si_adj - 4.5))) *
           tree_age**-1.4) + 4.5)
    
    ht_m = ht_ft * 0.3048
         
    return ht_m


def ht_red_alder(tree_age, si50ft):
    """Calculate the height of red alder given the tree age and
        the 20 year base site index height in feet. Equations are
        from Harrington and Worthington et al 1960."""    
    
    b0 = 0.60924
    b1 = 19.538
    
    # calculate breast height age. One year from Harrington and Curtis (1986)
    age_bh = tree_age - 1    
    
    ht_m = 1 / ((b0 + b1 / tree_age) / si50ft) * 0.3048
    
    return ht_m

# Species Code - Species - SI

# Conifer
# RC - Western Redcedar
# DF - Douglas Fir

# Hardwood/Shurb
# DG - Pacfic Dogwood (surrogate for Red Osier Dogwood) - (adj = 0.60)
# OT - Other (Oregon Ash) - 99
# WI - Willow - (adj = 0.50)
# CW - Black Cottonwood (adj = 0.85)
# RA - Red Alder
# BM - Big Leaf Maple - (adj = 0.75)

tree_age = 51

# Westside Cascades Variant
wc_redcedar = ht_western_redcedar(tree_age, site_index_50_m=35)
wc_doug_fir = ht_douglas_fir(tree_age, site_index_100_ft=111, adj=1)

wc_dogwood = ht_douglas_fir(tree_age, site_index_100_ft=73, adj=.60)
wc_or_ash = ht_douglas_fir(tree_age, site_index_100_ft=73, adj=.50)
wc_willow = ht_douglas_fir(tree_age, site_index_100_ft=73, adj=.50)
wc_redalder = ht_red_alder(tree_age, si50ft=90)
wc_cottonwood = ht_douglas_fir(tree_age, site_index_100_ft=73, adj=.85)
wc_bl_maple = ht_douglas_fir(tree_age, site_index_100_ft=73, adj=.75)

# Pacfic Northwest Coast Variant
pn_redcedar = ht_western_redcedar(tree_age, site_index_50_m=35)
pn_doug_fir = ht_douglas_fir(tree_age, site_index_100_ft=128, adj=1)

pn_dogwood = ht_douglas_fir(tree_age, site_index_100_ft=98, adj=.60)
pn_or_ash = ht_douglas_fir(tree_age, site_index_100_ft=98, adj=.50)
pn_willow = ht_douglas_fir(tree_age, site_index_100_ft=98, adj=.50)
pn_redalder = ht_red_alder(tree_age, si50ft=90)
pn_cottonwood = ht_douglas_fir(tree_age, site_index_100_ft=98, adj=.85)
pn_bl_maple = ht_douglas_fir(tree_age, site_index_100_ft=98, adj=.75)
