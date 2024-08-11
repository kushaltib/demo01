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


#to initialize the dataframe for storing the summary of near-term parameters
def init_neardata(country_list):

     columns = ['Year','Scope','Applies','Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB','Processed']
     data = pd.DataFrame(columns=columns,index=country_list)

     return data



#to extract values from NDC table and store it as a list:
 
def ndc_ref_data(country,ndc_table,ref,applies_to,format,scope,supp=False):

     NDC = ndc_table

     if supp:
          ref = 'Supp_'+ref
     
     data_list = [NDC.loc[country,ref+'_'+applies_to+'_'+format+'_'+scope],\
                       NDC.loc[country,'Target_'+applies_to+'_'+format+'_UB_unconditional_'+scope],\
                       NDC.loc[country,'Target_'+applies_to+'_'+format+'_LB_conditional_'+scope],\
                       NDC.loc[country,'Target_'+applies_to+'_'+format+'_UB_conditional_'+scope],\
                       'Yes'                       
                       ]
     return data_list
     




#this function summarizes country-wise future CO2eq or CO2 emissions for the NDC-year for Total-net or Total-excl
#for countries which directly report their emissions
#applies to = 'CO2' or 'CO2eq'

def grp_emission_abs(ndc_table,applies_to,country_list=None,data=None):

     NDC = ndc_table

     #choose the list of countries on which operation is to be carried out
     if country_list is None:
        country_list = NDC.index

     #create grouped list of countries     
     target_format = create_lists(country_list,NDC,'Target_format',NDC['Target_format'].unique().tolist())
     target_applies = create_lists(country_list,NDC,'Target_applies_to',NDC['Target_applies_to'].unique().tolist())
     target_scope = create_lists(country_list,NDC,'Target_scope',NDC['Target_scope'].unique().tolist()) 

     
     #check if a data table is provided for update else create empty dataframe to store future emissions by country:
     if data is None:  data = init_neardata(country_list)
     
     if not target_applies[applies_to]:
          print("No country with direct 'Emissions' values for NDC that applies to "+applies_to+"\n")

     else:
          print("Analysing countries with direct 'Emissions' values for NDC\n")

          for country in set(target_format['emissions']) & set(target_applies[applies_to]):
            #print(country)

            for scope in ['Total-net','Total-excl']:
                 
                 if country in target_scope[scope]:
                      data.loc[country] = [NDC.loc[country,'Target_year'],\
                                           NDC.loc[country,'Target_scope'],\
                                           applies_to,\
                                           NDC.loc[country,'Target_'+applies_to+'_emissions_LB_unconditional_'+scope],\
                                           NDC.loc[country,'Target_'+applies_to+'_emissions_UB_unconditional_'+scope],\
                                           NDC.loc[country,'Target_'+applies_to+'_emissions_LB_conditional_'+scope],\
                                           NDC.loc[country,'Target_'+applies_to+'_emissions_UB_conditional_'+scope],\
                                           'Yes'                       
                                           ]
                      
                      
               
            #replace NaN for cond emissions if there is an uncond emission
            if is_nan(data.loc[country,'Conditional_LB']):
               data.loc[country,'Conditional_LB'] = data.loc[country,'Unconditional_LB']
               data.loc[country,'Conditional_UB'] = data.loc[country,'Unconditional_UB']
                 





          processsed_data = data[data['Processed']=='Yes']
          print("\n",len(processsed_data.index)," countries have been processed out of total:",len(country_list))       
          
     return data


#this function summarizes country-wise future CO2eq or CO2 emissions for the NDC-year for Total-net or Total-excl
#for countries which report in terms of percent reduction w.r.t BASE year or BAU.

def grp_percent_abs(ndc_table,applies_to,co2_hist,co2eq_hist,hist_luc,country_list=None,data=None):

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
     if data is None:  data = init_neardata(country_list)


     
     if not target_applies[applies_to]:
          print("No country with 'percent reduction target' for NDC that applies to "+applies_to+"\n")

     else:
          print("Analyzing countries with percent reduction target \n")

          for REF in ['BAU','Base']:

               print("\nReading data for countries with 'Reduction relative to "+REF+"' \n")

               for country in set(target_applies[applies_to]) & set(target_type['absolute']) & set(target_format['percent']) & set(target_reference[REF]):

                    for scope in ['Total-net','Total-excl']:

                         #initiate reference emissions as nan:
                         emiss_ref=np.nan

                         #collect reference emissions:
                         if NDC.loc[country,REF]=='Yes':
                              emiss_ref = NDC.loc[country,REF+'_'+applies_to+'_emissions_'+scope]
                         elif NDC.loc[country,'Supp_'+REF]=='Yes':
                              emiss_ref = NDC.loc[country,'Supp_'+REF+'_'+applies_to+'_emissions_'+scope]
                         else: 
                              if REF=='Base':
                                   #take base year emissions from inventory
                                   if applies_to=='CO2': emiss_ref = co2_hist.loc[country,NDC.loc[country,REF+'_year']]/1000
                                   if applies_to=='CO2eq': emiss_ref = co2eq_hist.loc[country,NDC.loc[country,REF+'_year']]/1000

                                   #add LUC emissions if Total-net
                                   luc_st_yr = hist_luc.loc[country].index[0]
                                   if luc_st_yr>NDC.loc[country,REF+'_year']:
                                        yr = luc_st_yr
                                   else:
                                        yr = NDC.loc[country,REF+'_year']


                                   if scope=='Total-net': emiss_ref = emiss_ref+hist_luc.loc[country,yr]


                    


                         if not is_nan(emiss_ref): #if reference emission is not nan then only proceed

                              #print(country)
                         
                              if country in target_scope[scope]:
                                   uncond_lb = emiss_ref*(1-NDC.loc[country,'Target_'+applies_to+'_percent_UB_unconditional_'+scope]/100)
                                   uncond_ub = emiss_ref*(1-NDC.loc[country,'Target_'+applies_to+'_percent_LB_unconditional_'+scope]/100)
                                   cond_lb = emiss_ref*(1-NDC.loc[country,'Target_'+applies_to+'_percent_UB_conditional_'+scope]/100)
                                   cond_ub = emiss_ref*(1-NDC.loc[country,'Target_'+applies_to+'_percent_LB_conditional_'+scope]/100)

                                   data.loc[country] = [NDC.loc[country,'Target_year'],\
                                                        NDC.loc[country,'Target_scope'],\
                                                        applies_to,\
                                                        uncond_lb,\
                                                        uncond_ub,\
                                                        cond_lb,\
                                                        cond_ub,\
                                                        'Yes'
                                                        ]
                                   
                                   #replace NaN for cond emissions with uncond emission
                                   if is_nan(data.loc[country,'Conditional_LB']):
                                        data.loc[country,'Conditional_LB'] = data.loc[country,'Unconditional_LB']
                                        data.loc[country,'Conditional_UB'] = data.loc[country,'Unconditional_UB']
                 
                      
       
          processsed_data = data[data['Processed']=='Yes']
          print("\n",len(processsed_data.index)," countries have been processed out of total:",len(country_list))       
          
     return data



#this function summarizes country-wise future CO2eq or CO2 emissions for the NDC-year for Total-net or Total-excl
#for countries which report in terms of percent reduction w.r.t BASE year or BAU.

def grp_percent_int(ndc_table,applies_to,co2_hist,co2eq_hist,hist_luc,gdp,country_list=None,data=None):

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
     if data is None:  data = init_neardata(country_list)

     
     if not target_applies[applies_to]:
          print("No country intensity targets for NDC that applies to "+applies_to+"\n")

     else:
          print("Analyzing countries with intensity target \n")

          for REF in ['BAU','Base']:            

               print("\nReading data for countries with 'Reduction relative to "+REF+"' \n")


               for country in set(target_applies[applies_to]) & set(target_type['intensity']) & set(target_format['percent']) & set(target_reference[REF]):

                    for scope in ['Total-net','Total-excl']:

                         #initiate ref intensity:
                         ref_int = np.nan

                         #collect reference emissions
                         if NDC.loc[country,REF]=='Yes':
                              emiss_ref = NDC.loc[country,REF+'_'+applies_to+'_emissions_'+scope]
                         elif NDC.loc[country,'Supp_'+REF]=='Yes':
                              emiss_ref = NDC.loc[country,'Supp_'+REF+'_'+applies_to+'_emissions_'+scope]
                         else: 
                              if REF=='Base': #take base year emissions from inventory
                                   if applies_to=='CO2': emiss_ref = co2_hist.loc[country,NDC.loc[country,REF+'_year']]/1000
                                   if applies_to=='CO2eq': emiss_ref = co2eq_hist.loc[country,NDC.loc[country,REF+'_year']]/1000

                                   #add LUC emissions if Total-net
                                   luc_st_yr = hist_luc.loc[country].index[0]
                                   if luc_st_yr>NDC.loc[country,REF+'_year']:
                                        yr = luc_st_yr
                                   else:
                                        yr = NDC.loc[country,REF+'_year']


                                   if scope=='Total-net': emiss_ref = emiss_ref+hist_luc.loc[country,yr]
                         
                         #collect reference and target GDP
                         
                         if NDC.loc[country,'GDP']=='Yes':
                              gdp_ref = NDC.loc[country,REF+'_GDP']
                              gdp_tar_lb = NDC.loc[country,'Target_GDP_LB']
                              gdp_tar_ub = NDC.loc[country,'Target_GDP_UB']

                         elif NDC.loc[country,'Supp_GDP']=='Yes':
                              gdp_ref =  NDC.loc[country,'Supp_'+REF+'_GDP']
                              gdp_tar_lb = NDC.loc[country,'Supp_Target_GDP_LB']
                              gdp_tar_ub = NDC.loc[country,'Supp_Target_GDP_UB']
                         else:
                              gdp_ref = gdp.loc[country,NDC.loc[country,REF+'_year']]
                              gdp_tar_lb = gdp.loc[country,NDC.loc[country,'Target_year']]
                              gdp_tar_ub = gdp.loc[country,NDC.loc[country,'Target_year']]

                         ref_int = emiss_ref/gdp_ref

                         if not is_nan(ref_int): #if reference intentisty is not nan then only proceed
                              
                              #print(country)

                              print(country," | REF intensity |", ref_int)
                                                            
                              #calculate the target emissions
                              uncond_lb = ref_int*(1-NDC.loc[country,'Target_'+applies_to+'_percent_UB_unconditional_'+scope]/100)*gdp_tar_lb
                              uncond_ub = ref_int*(1-NDC.loc[country,'Target_'+applies_to+'_percent_LB_unconditional_'+scope]/100)*gdp_tar_ub
                              cond_lb = ref_int*(1-NDC.loc[country,'Target_'+applies_to+'_percent_UB_conditional_'+scope]/100)*gdp_tar_lb
                              cond_ub = ref_int*(1-NDC.loc[country,'Target_'+applies_to+'_percent_LB_conditional_'+scope]/100)*gdp_tar_ub

                              data.loc[country] = [NDC.loc[country,'Target_year'],\
                                                   NDC.loc[country,'Target_scope'],\
                                                   applies_to,\
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
          print("\n",len(processsed_data.index)," countries have been processed out of total:",len(country_list))       
          
     return data





#this function adjusts country-wise future CO2eq or CO2 emissions for the NDC-year for Total-excl
#for countries which report in terms of Total-net
def to_total_excl(ndc_table,hist_luc,data=None):

     NDC = ndc_table

     if data is None:
          print("Please push the data summary for adjusting to Total-excl")
     
     else:
          data_adj = data.copy()
          country_list = data.index

          #initialize dataframe to store luc info
          data_luc = init_neardata(country_list)

          country_for_adjust = create_lists(country_list,data,'Scope',data['Scope'].unique().tolist())
          luc_separate = create_lists(country_list,NDC,'LULUCF_separate_info',NDC['LULUCF_separate_info'].unique().tolist())
          luc_supp_info = create_lists(country_list,NDC,'Supp_LULUCF_separate_info',NDC['Supp_LULUCF_separate_info'].unique().tolist())

          non_luc_countries = ['Int. Aviation', 'Int. Shipping']
          # Create a new country list without the non luc countries
          country_list = [country for country in data.loc[data['Processed']=='Yes'].index if country not in non_luc_countries]

          
          
          for country in country_list:
               
               applies_to = data.loc[country,'Applies']

               if country in luc_separate['Yes']:
                    adj_uncond_lb = NDC.loc[country,'Target_'+applies_to+'_emissions_LB_unconditional_LULUCF']
                    adj_uncond_ub = NDC.loc[country,'Target_'+applies_to+'_emissions_UB_unconditional_LULUCF']
                    adj_cond_lb = NDC.loc[country,'Target_'+applies_to+'_emissions_LB_conditional_LULUCF']
                    adj_cond_ub = NDC.loc[country,'Target_'+applies_to+'_emissions_UB_conditional_LULUCF']

               elif country in luc_supp_info['Yes']:
                    adj_uncond_lb = NDC.loc[country,'Supp_Target_'+applies_to+'_emissions_LB_unconditional_LULUCF']
                    adj_uncond_ub = NDC.loc[country,'Supp_Target_'+applies_to+'_emissions_UB_unconditional_LULUCF']
                    adj_cond_lb = NDC.loc[country,'Supp_Target_'+applies_to+'_emissions_LB_conditional_LULUCF']
                    adj_cond_ub = NDC.loc[country,'Supp_Target_'+applies_to+'_emissions_UB_conditional_LULUCF']
               
               else:
                    adj_uncond_lb = hist_luc.loc[country,hist_luc.columns[-1]]/1000
                    adj_uncond_ub = hist_luc.loc[country,hist_luc.columns[-1]]/1000
                    adj_cond_lb = hist_luc.loc[country,hist_luc.columns[-1]]/1000
                    adj_cond_ub = hist_luc.loc[country,hist_luc.columns[-1]]/1000                   
                    
               

               if is_nan(adj_cond_lb): adj_cond_lb = adj_uncond_lb
               if is_nan(adj_cond_ub): adj_cond_ub = adj_uncond_ub

               data_luc.loc[country] = [data.loc[country,'Year'],\
                                        'LUC',\
                                        applies_to,\
                                        adj_uncond_lb,\
                                        adj_uncond_ub,\
                                        adj_cond_lb,\
                                        adj_cond_ub,\
                                        'Yes'
                                        ]
          
                  

               if country in country_for_adjust['Total-net']:

                    data_adj.loc[country,'Scope'] = 'Total-excl'

                    data_adj.loc[country,'Unconditional_LB'] = min(data.loc[country,'Unconditional_LB']-adj_uncond_lb,data.loc[country,'Unconditional_LB']-adj_uncond_ub)
                    data_adj.loc[country,'Unconditional_UB'] = max(data.loc[country,'Unconditional_UB']-adj_uncond_lb,data.loc[country,'Unconditional_UB']-adj_uncond_lb)
                    data_adj.loc[country,'Conditional_LB'] = min(data.loc[country,'Conditional_LB']-adj_cond_lb,data.loc[country,'Conditional_LB']-adj_cond_ub)
                    data_adj.loc[country,'Conditional_UB'] = max(data.loc[country,'Conditional_UB']-adj_cond_lb,data.loc[country,'Conditional_UB']-adj_cond_ub)

                    if is_nan(data_adj.loc[country,'Conditional_LB']):
                         data_adj.loc[country,'Conditional_LB'] = data_adj.loc[country,'Unconditional_LB']
                         data_adj.loc[country,'Conditional_UB'] = data_adj.loc[country,'Unconditional_UB']

               



     return data_adj,data_luc          
               
#applies_to = ALL, CO2eq or CO2
def create_ndc_table(ndc_table,hist_luc,co2_hist,co2eq_hist,gdp,applies_to='ALL',country_list=None):
     
     NDC = ndc_table

     #choose the list of countries on which operation is to be carried out
     if country_list is None:
        country_list = NDC.index

     data_ndc = init_neardata(country_list)

     if applies_to=='ALL' or applies_to=='CO2eq':
          data_ndc = grp_emission_abs(NDC,'CO2eq',country_list,data_ndc)
          data_ndc = grp_percent_abs(NDC,'CO2eq',co2_hist,co2eq_hist,hist_luc,country_list,data_ndc)
          data_ndc = grp_percent_int(NDC,'CO2eq',co2_hist,co2eq_hist,hist_luc,gdp,country_list,data_ndc)
                  

     if applies_to=='ALL' or applies_to=='CO2':

          data_ndc = grp_emission_abs(NDC,'CO2',country_list,data_ndc)
          data_ndc = grp_percent_abs(NDC,'CO2',co2_hist,co2eq_hist,hist_luc,country_list,data_ndc)
          data_ndc = grp_percent_int(NDC,'CO2',co2_hist,co2eq_hist,hist_luc,gdp,country_list,data_ndc)
          

     
     data_ndc_noluc,data_luc = to_total_excl(NDC,hist_luc,data=data_ndc)

     not_processsed_data = data_ndc_noluc[data_ndc_noluc['Processed']!='Yes']
     print("\n",len(not_processsed_data.index)," countries have not been processed out of total:",len(country_list))

     for country in not_processsed_data.index:
          print(country)




     return data_ndc,data_ndc_noluc,data_luc



     



     







#--END--


