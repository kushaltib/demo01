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


def co2_nz(ndc_table,ch4_summ,n2o_summ,country_list=None,data=None):

     NDC = ndc_table

     #choose the list of countries on which operation is to be carried out
     if country_list is None:
        country_list = NDC.index

     #create grouped list of countries     
     nz = create_lists(country_list,NDC,'Neutrality',NDC['Neutrality'].unique().tolist())
     nz_applies = create_lists(country_list,NDC,'Neutrality_applies_to',NDC['Neutrality_applies_to'].unique().tolist())

     if data is None:
          columns = ['Neutrality','Year','CO2_nz_uncond_lb','CO2_nz_uncond_ub','CO2_nz_cond_lb','CO2_nz_cond_ub','Processed']
          data = pd.DataFrame(columns=columns,index=country_list)
          

     for country in set(nz['Yes']):

          if country in nz_applies['CO2eq']:

               data.loc[country,'Neutrality'] = NDC.loc[country,'Neutrality']
               data.loc[country,'Year'] = NDC.loc[country,'Neutrality_year']
               data.loc[country,'CO2_nz_uncond_lb'] = -ch4_summ.loc[country,'Unconditional_LB']*28-n2o_summ.loc[country,'Unconditional_LB']*265
               data.loc[country,'CO2_nz_uncond_ub'] = -ch4_summ.loc[country,'Unconditional_UB']*28-n2o_summ.loc[country,'Unconditional_UB']*265
               data.loc[country,'CO2_nz_cond_lb'] = -ch4_summ.loc[country,'Conditional_LB']*28-n2o_summ.loc[country,'Conditional_LB']*265
               data.loc[country,'CO2_nz_cond_ub'] = -ch4_summ.loc[country,'Conditional_UB']*28-n2o_summ.loc[country,'Conditional_UB']*265
               data.loc[country,'Processed'] = 'Yes'
          
          if country in nz_applies['CO2']:

               data.loc[country,'Neutrality'] = NDC.loc[country,'Neutrality']
               data.loc[country,'Year'] = NDC.loc[country,'Neutrality_year']
               data.loc[country,'CO2_nz_uncond_lb'] = 0
               data.loc[country,'CO2_nz_uncond_ub'] = 0
               data.loc[country,'CO2_nz_cond_lb'] = 0
               data.loc[country,'CO2_nz_cond_ub'] = 0
               data.loc[country,'Processed'] = 'Yes'

     return data






     


#--END--


