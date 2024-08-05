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

#constants:

#--GWP values from IPCC 5th report
GWP_CH4 = 28.0
GWP_N2O = 265.0



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


#to initialize the dataframe for storing the summary of near-term parameters
def init_near_nonco2(ndc_summ):

     columns = ['Year','Gas','Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB','Processed']
     near_nonco2 = pd.DataFrame(columns=columns,index=ndc_summ.index)

     return near_nonco2



       
#calculate default N2O: constant as last year of inventory

def  def_n2o(ndc_table,ndc_summ,n2o_hist,data=None):
      
      #NDC = ndc_table     


      if data is None:  data = init_near_nonco2(ndc_summ)

      

      for country in ndc_summ.index:
            
                        
                       
            #collect historical n2o emissions
            m_hist = n2o_hist.loc[country]

            
            #last inventory year:
            emis_last=m_hist.values[-1]/1000         #since historical emission are in kT and NDC summary tables are in Mt.
            #yr_last = m_hist.index[-1] 

            #ndc year:
            yr_near = ndc_summ.loc[country,'Year']
            
            #estimate N2O 
            uncond_lb = emis_last
            uncond_ub = emis_last
            cond_lb = emis_last
            cond_ub = emis_last

            data.loc[country] = [yr_near,\
                                 'N2O',\
                                 uncond_lb,\
                                 uncond_ub,\
                                 cond_lb,\
                                 cond_ub,\
                                 'Yes'
                                 ]

      return data

      

      
    




#--END--
