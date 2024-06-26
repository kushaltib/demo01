# -*- coding: utf-8 -*-

#--import python packages
import warnings
import sys
import pandas as pd
import numpy as np
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.optimize import minimize, curve_fit, OptimizeWarning
import pathlib
import argparse
#

#--keep the warnings silent
warnings.simplefilter("ignore", OptimizeWarning)

#to filter out nan entries in a string list
def is_nan(x):
    return isinstance(x, float) and math.isnan(x)


#to create lists of different target criteria
def create_lists(country_list,table,group_name,group):
 
    #remove nan from the list:
    group = [x for x in group if not is_nan(x)]

    #create emptry dictionary for storing the grouped lists
    lists = {}

    for element in group:
        lists[element] = []

        for country in country_list:
                    if table.loc[country,group_name]==element: lists[element].append(country)


    return lists


#--function to compute emissions using the simple model by --Edwards et al, Environmental Science & Policy, 66, 191-198, 2016
#--doi: 10.1016/j.envsci.2016.08.013

#--E0: emission at initial year
#--g0: growth rate of emissions at initial year
#--Eneg: asymptotic emissions (can be negative but does not have to be)
#--dg: yearly increment in growth rate
def emi_calc(year_start=2022,E0,g0,gmax=0.1,Eneg,dg):
    #--initialising to latest-year values
    emi_list=[E0]  #--list of yearly emission values
    g=g0           #--growth rate
    g_list=[g]     #--list of yearly g values
    #--loop on years 2021 to 2100
    for yr in range(year_start,2101):
        #--emissions in year yr as per Edwards et al
        emi=Eneg+(E0-Eneg)*np.exp(np.sum(np.array(g_list,dtype=object))) 
        #--emission is appended to list
        emi_list.append(emi)
        #--growth rate is reduced linearly
        g=g-dg
        #--growth rate cannot be less than -gmax (-10%)
        g=max(g,-gmax)
        #--growth rate is appended to list
        g_list.append(g)
    #--return list of emissions
    return emi_list
#
#--cost function to compute mismatch to our targets
#--x: control vector (g0, Eneg, dg)
#--E0: emission at initial year
#--gi0: a priori value of growth rate at initial year
#--E2030: emission target for 2030
#--Elong: emission target for yr_long (e.g. 0 if neutrality)
#--yr_long: target year for long-term target
def cost(x,E0,gi0,E2030,Elong,yr_long):
    #--decomposing control vector
    g0=x[0]          #--growth rate in 2018 (can be optimised)
    Eneg=x[1]+Elong  #--asymptotic emissions
    dg=x[2]          #--change in growth rate year on year
    #--compute emission time profile
    emi_list=emi_calc(E0,g0,Eneg,dg)
    #--compute simulated year for long-term target
    if first_neg(emi_list,Elong) != None:
        yr_long_simulated=yr_last+first_neg(emi_list,Elong)
    else:
        yr_long_simulated=yr_last
    #--compute cost function as departure from g0, 2030 target, long-term target and long-term target year
    #--each term of the cost function is weighted by a reasonable value
    err=10.*((emi_list[2030-yr_last]-E2030)/E0)**2 + 5.*((emi_list[yr_long-yr_last]-Elong)/E0)**2. + \
        ((yr_long_simulated-yr_long)/10.)**2. + ((g0-gi0)/gi0)**2.
    return err


















#this function summarizes country-wise neutraility CO2eq for Total-excl* (*for now  - needs user input/range)
def grp_nz(ndc_table,country_list=None,data=None,process='all'):

     NDC = ndc_table

     #choose the list of countries on which operation is to be carried out
     if country_list is None:
        country_list = NDC.index

     #create grouped list of countries     
     nz = create_lists(country_list,NDC,'Neutrality',NDC['Neutrality'].unique().tolist())
     nz_applies = create_lists(country_list,NDC,'Neutrality_applies_to',NDC['Neutrality_applies_to'].unique().tolist())

     if data is None:
          columns = ['Neutrality','Year','co2eq_excl','co2eq_net','co2_excl','co2_net','Processed']
          data = pd.DataFrame(columns=columns,index=country_list)
          

     for country in set(nz['Yes']):
          if process=='all' or process=='co2eq':
               if country in nz_applies['CO2eq']:
                    data.loc[country,'Neutrality'] = NDC.loc[country,'Neutrality']
                    data.loc[country,'Year'] = NDC.loc[country,'Neutrality_year']
                    data.loc[country,'co2eq_excl'] = 0
                    data.loc[country,'co2eq_net'] = 0
                    data.loc[country,'Processed'] = 'Yes'
          
          if process=='all' or process=='co2':
               if country in nz_applies['CO2']:
                    data.loc[country,'Neutrality'] = NDC.loc[country,'Neutrality']
                    data.loc[country,'Year'] = NDC.loc[country,'Neutrality_year']
                    data.loc[country,'co2_excl'] = 0
                    data.loc[country,'co2_net'] = 0
                    data.loc[country,'Processed'] = 'Yes'

     
     return data
     


#--END--


