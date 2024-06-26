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

#this function summarizes country-wise future CO2eq or CO2 emissions for the NDC-year for Total-net or Total-excl
#for countries which directly report their emissions
def grp_emiss(ndc_table,applies_to,country_list=None,data=None):

     NDC = ndc_table

     #choose the list of countries on which operation is to be carried out
     if country_list is None:
        country_list = NDC.index

     #create grouped list of countries     
     target_format = create_lists(country_list,NDC,'Target_format',NDC['Target_format'].unique().tolist())
     target_applies = create_lists(country_list,NDC,'Target_applies_to',NDC['Target_applies_to'].unique().tolist())
     target_scope = create_lists(country_list,NDC,'Target_scope',NDC['Target_scope'].unique().tolist()) 


     
     #check if a data table is provided for update else create empty dataframe to store future emissions by country:
     if data is None:
          columns = ['Year','Scope','Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB','Processed']
          data = pd.DataFrame(columns=columns,index=country_list)


     
     if not target_applies[applies_to]:
          print("No country with direct 'Emissions' values for the future that applies to "+applies_to+"\n")

     else:
          print("Collating "+applies_to+" for",len(target_applies[applies_to])," countries with direct 'Emissions' values for the future\n")

          for country in set(target_format['emissions']) & set(target_applies[applies_to]):
            print(country)

            if country in target_scope['Total-net']:
                 data.loc[country] = [NDC.loc[country,'Target_year'],\
                                       NDC.loc[country,'Target_scope'],\
                                       NDC.loc[country,'Target_'+applies_to+'_emissions_LB_unconditional_Total-net'],\
                                       NDC.loc[country,'Target_'+applies_to+'_emissions_UB_unconditional_Total-net'],\
                                       NDC.loc[country,'Target_'+applies_to+'_emissions_LB_conditional_Total-net'],\
                                       NDC.loc[country,'Target_'+applies_to+'_emissions_UB_conditional_Total-net'],\
                                       'Yes'                       
                                      ]
                 
            if country in target_scope['Total-excl']:
                 data.loc[country] = [NDC.loc[country,'Target_year'],\
                                       NDC.loc[country,'Target_scope'],\
                                       NDC.loc[country,'Target_'+applies_to+'_emissions_LB_unconditional_Total-excl'],\
                                       NDC.loc[country,'Target_'+applies_to+'_emissions_UB_unconditional_Total-excl'],\
                                       NDC.loc[country,'Target_'+applies_to+'_emissions_LB_conditional_Total-excl'],\
                                       NDC.loc[country,'Target_'+applies_to+'_emissions_UB_conditional_Total-excl'],\
                                       'Yes'                       
                                      ]
                 
            #replace NaN for cond emissions if there is an uncond emission
            if is_nan(data.loc[country,'Conditional_LB']):
               data.loc[country,'Conditional_LB'] = data.loc[country,'Unconditional_LB']
               data.loc[country,'Conditional_UB'] = data.loc[country,'Unconditional_UB']
                 





          processsed_data = data[data['Processed']=='Yes']
          print("\n",len(processsed_data.index)," countries have been processed out of ",len(country_list))       
          
     return data


#this function summarizes country-wise future CO2eq or CO2 emissions for the NDC-year for Total-net or Total-excl
#for countries which report in terms of percent reduction w.r.t BASE year or BAU.

def grp_percent_abs(ndc_table,applies_to,country_list=None,data=None):

     NDC = ndc_table

     #choose the list of countries on which operation is to be carried out
     if country_list is None:
        country_list = NDC.index

     #create grouped list of countries
     target = ['Target_type','Target_format','Target_applies_to','Target_scope','Target_reference']
          
     target_type = create_lists(country_list,NDC,target[0],NDC[target[0]].unique().tolist())
     target_format = create_lists(country_list,NDC,target[1],NDC[target[1]].unique().tolist())
     target_applies = create_lists(country_list,NDC,target[2],NDC[target[2]].unique().tolist())
     target_scope = create_lists(country_list,NDC,target[3],NDC[target[3]].unique().tolist())
     target_reference = create_lists(country_list,NDC,target[4],NDC[target[4]].unique().tolist())
     
     #check if a data table is provided for update else create empty dataframe to store future emissions by country:
     if data is None:
          columns = ['Year','Scope','Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB','Processed']
          data = pd.DataFrame(columns=columns,index=country_list)


     
     if not target_applies[applies_to]:
          print("No country with direct 'Emissions' values for the future that applies to "+applies_to+"\n")

     else:
          print("Collating "+applies_to+" for",len(target_applies[applies_to])," countries with percent reduction target \n")

          for reference in ['bau','base']:

               if reference=='bau': REF ='BAU'
               else: REF = 'Base'               

               print("\nReading data for countries with 'Reduction relative to "+reference+"' \n")

               for country in set(target_applies['CO2eq']) & set(target_type['absolute']) & set(target_format['percent']) & set(target_reference[reference]):
                    #check if reference is present:

                    if NDC.loc[country,REF]=='Yes':

                         print(country)

                         if country in target_scope['Total-net']:
                              uncond_lb = NDC.loc[country,REF+'_'+applies_to+'_emissions_Total-net']*(1-NDC.loc[country,'Target_'+applies_to+'_percent_UB_unconditional_Total-net']/100)
                              uncond_ub = NDC.loc[country,REF+'_'+applies_to+'_emissions_Total-net']*(1-NDC.loc[country,'Target_'+applies_to+'_percent_LB_unconditional_Total-net']/100)
                              cond_lb = NDC.loc[country,REF+'_'+applies_to+'_emissions_Total-net']*(1-NDC.loc[country,'Target_'+applies_to+'_percent_UB_conditional_Total-net']/100)
                              cond_ub = NDC.loc[country,REF+'_'+applies_to+'_emissions_Total-net']*(1-NDC.loc[country,'Target_'+applies_to+'_percent_LB_conditional_Total-net']/100)

                              data.loc[country] = [NDC.loc[country,'Target_year'],\
                                                   NDC.loc[country,'Target_scope'],\
                                                   uncond_lb,\
                                                   uncond_ub,\
                                                   cond_lb,\
                                                   cond_ub,\
                                                   'Yes'
                                                   ]
                              
                         if country in target_scope['Total-excl']:
                              uncond_lb = NDC.loc[country,REF+'_'+applies_to+'_emissions_Total-excl']*(1-NDC.loc[country,'Target_'+applies_to+'_percent_UB_unconditional_Total-excl']/100)
                              uncond_ub = NDC.loc[country,REF+'_'+applies_to+'_emissions_Total-excl']*(1-NDC.loc[country,'Target_'+applies_to+'_percent_LB_unconditional_Total-excl']/100)
                              cond_lb = NDC.loc[country,REF+'_'+applies_to+'_emissions_Total-excl']*(1-NDC.loc[country,'Target_'+applies_to+'_percent_UB_conditional_Total-excl']/100)
                              cond_ub = NDC.loc[country,REF+'_'+applies_to+'_emissions_Total-excl']*(1-NDC.loc[country,'Target_'+applies_to+'_percent_LB_conditional_Total-excl']/100)

                              data.loc[country] = [NDC.loc[country,'Target_year'],\
                                                   NDC.loc[country,'Target_scope'],\
                                                   uncond_lb,\
                                                   uncond_ub,\
                                                   cond_lb,\
                                                   cond_ub,\
                                                   'Yes'
                                                  ]
                         #replace NaN for cond emissions if there is an uncond emission     
                         if is_nan(data.loc[country,'Conditional_LB']):
                              data.loc[country,'Conditional_LB'] = data.loc[country,'Unconditional_LB']
                              data.loc[country,'Conditional_UB'] = data.loc[country,'Unconditional_UB']
                 
                      
       
          processsed_data = data[data['Processed']=='Yes']
          print("\n",len(processsed_data.index)," countries have been processed out of ",len(country_list))       
          
     return data


#this function adjusts country-wise future CO2eq or CO2 emissions for the NDC-year for Total-excl
#for countries which report in terms of Total-net
def to_total_excl(ndc_table,applies_to,data=None):

     NDC = ndc_table

     if data is None:
          print("Please push the data summary for adjusting to Total-excl")
     
     else:
          data_adj = data.copy()
          country_list = data.index

          country_for_adjust = create_lists(country_list,data,'Scope',data['Scope'].unique().tolist())
          luc_separate = create_lists(country_list,NDC,'LULUCF_separate_info',NDC['LULUCF_separate_info'].unique().tolist())

          for country in country_for_adjust['Total-net']:
               if country in luc_separate:
                    adj_uncond_lb = NDC.loc[country,'Target_'+applies_to+'_emissions_LB_unconditional_LULUCF']
                    adj_uncond_ub = NDC.loc[country,'Target_'+applies_to+'_emissions_UB_unconditional_LULUCF']
                    adj_cond_lb = NDC.loc[country,'Target_'+applies_to+'_emissions_LB_conditional_LULUCF']
                    adj_cond_ub = NDC.loc[country,'Target_'+applies_to+'_emissions_UB_conditional_LULUCF']

               else:
                    adj_uncond_lb = NDC.loc[country,'Supp_Target_'+applies_to+'_emissions_LB_unconditional_LULUCF']
                    adj_uncond_ub = NDC.loc[country,'Supp_Target_'+applies_to+'_emissions_UB_unconditional_LULUCF']
                    adj_cond_lb = NDC.loc[country,'Supp_Target_'+applies_to+'_emissions_LB_conditional_LULUCF']
                    adj_cond_ub = NDC.loc[country,'Supp_Target_'+applies_to+'_emissions_UB_conditional_LULUCF']

                    
                    
                    
               data_adj.loc[country,'Scope'] = 'Total-excl'
               data_adj.loc[country,'Unconditional_LB'] = data.loc[country,'Unconditional_LB']-adj_uncond_lb
               data_adj.loc[country,'Unconditional_UB'] = data.loc[country,'Unconditional_UB']-adj_uncond_ub
               data_adj.loc[country,'Conditional_LB'] = data.loc[country,'Conditional_LB']-adj_cond_lb
               data_adj.loc[country,'Conditional_UB'] = data.loc[country,'Conditional_UB']-adj_cond_ub

               if is_nan(data_adj.loc[country,'Conditional_LB']):
                  
                  data_adj.loc[country,'Conditional_LB'] = data_adj.loc[country,'Unconditional_LB']
                  data_adj.loc[country,'Conditional_UB'] = data_adj.loc[country,'Unconditional_UB']



     return data_adj          
               




     







#--END--


