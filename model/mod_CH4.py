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


#-------------------------------------------------------------------------------------------------
#FOR METHANE:
#-------------------------------------------------------------------------------------------------


#--Countries on the COP26 Global Methane Pledge (Countries joining the Global Methane Pledge commit to a 
#--collective goal of reducing global methane emissions by at least 30 percent from 2020 levels by 2030).
#--see https://ec.europa.eu/commission/presscorner/detail/en/statement_21_5766
#--methane scenario: inc=GMD is included in CO2eq pledges, add=GMD is additional to CO2eq pledges, def=default
#
countries_GMP=['EU27','United States','Albania','Andorra','Antigua and Barbuda','Argentina','Armenia','Barbados','Australia',\
                'Bahrain','Bangladesh','Barbados','Belize','Benin','Bosnia and Herzegovina','Brazil','Burkina Faso',\
                'Cape Verde','Cambodia','Cameroon','Canada','Central African Republic','Chad',\
                'Chile','Colombia','Comoros','Congo','Congo_the Democratic Republic of the','Cook Islands','Costa Rica',"Cote d'Ivoire",'Cuba',\
                'Denmark','Djibouti','Dominica','Dominican Republic',\
                'Ecuador','Egypt','El Salvador','Equatorial Guinea','Eswatini','Ethiopia',\
                'Fiji','Gabon','Gambia','Georgia','Ghana','Grenada','Guatemala','Guyana',\
                'Honduras', 'Iceland','Indonesia','Iraq','Ireland','Israel','Jamaica','Japan','Jordan',\
                'Korea, Republic of','Kyrgyzstan','Kuwait','Lebanon','Lesotho','Liberia','Libyan Arab Jamahiriya','Liechtenstein',\
                'Malawi','Malaysia','Mali','Marshall Islands','Mauritania','Mexico','Micronesia, Federated States of',\
                'Moldova, Republic of','Monaco','Mongolia','Montenegro','Morocco','Mozambique',\
                'Namibia','Nauru','Nepal','New Zealand','Niger','Nigeria','Niue','Macedonia, the former Yugoslav Republic of','Norway',\
                'Oman','Pakistan','Palau','Panama','Papua New Guinea','Peru','Philippines','Qatar','Rwanda',\
                'Saint Kitts and Nevis','Saint Lucia','Samoa','Sao Tome and Principe','Saudi Arabia','Senegal','Serbia','Seychelles',\
                'Sierra Leone','Singapore','Solomon Islands','Somalia','Sri Lanka','Sudan','Suriname','Switzerland',\
                'Timor-Leste','Togo','Tonga','Trinidad and Tobago','Tunisia','Tuvalu',\
                'Ukraine','United Arab Emirates','United Kingdom','Uruguay','Uzbekistan','Vanuatu','Viet Nam','Yemen','Zambia']


#--------------------------------------------------------------------------------------------------------------------------------------------------
#--EU27
EU27=['Austria','Belgium','Bulgaria','Croatia','Cyprus','Czech Republic','Denmark','Estonia','Finland','France',\
      'Germany','Greece','Hungary','Ireland','Italy','Latvia','Lithuania','Luxembourg','Malta','Netherlands','Poland',\
      'Portugal','Romania','Slovakia','Slovenia','Spain','Sweden']





#to update methane pledge list 
def add_to_GMP(country_list):
      #add only if not already in the GMP
      for country in country_list:
            if country not in countries_GMP: countries_GMP.append(country)
            

       
#calculate default CH4 based on NDC 2030 target of CO2 or CO2eq:
#proportionality year type: 'base' or 'custom'

def  def_ch4(ndc_table,ndc_summ,ch4_hist,co2_hist,co2eq_hist,data=None,prop_year_type='custom',prop_year=2005):
      
      NDC = ndc_table     


      if data is None:  data = init_near_nonco2(ndc_summ)

      #create list of countries which are processed:
      processed = create_lists(ndc_summ.index,ndc_summ,'Processed',['Yes'])      

      #for country in ndc_summ.index:
      for country in set(processed['Yes']):
                      
                        
            #collect historical co2 or coeq emissions
            if ndc_summ.loc[country,'Applies']=='CO2': c_hist = co2_hist.loc[country]/1000
            if ndc_summ.loc[country,'Applies']=='CO2eq': c_hist = co2eq_hist.loc[country]/1000

            
            
            #collect ndc co2 or co2eq emissions
            cndc = ndc_summ.loc[country,['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB']]


            
            #collect historical methane emissions
            m_hist = ch4_hist.loc[country]/1000

            #set relevant years 

            # proportionaility year:
            if prop_year_type=='base': prop_year = NDC.loc[country,'Base_year']
            if prop_year_type=='custom': prop_year = prop_year

            #last inventory year:
            yr_last = c_hist.index[-1]

            #ndc year:
            yr_near = ndc_summ.loc[country,'Year']
            
            #--precalculated CH4 emissions in 2030 following Inventory trend
            pre_mndc= ((yr_near-prop_year)/(yr_last-prop_year))*(m_hist.loc[yr_last]-m_hist.loc[prop_year]) + m_hist.loc[prop_year]

            #--precalculated CO2 or CO2eq emissions in 2030 following Inventory trend
            pre_cndc = ((yr_near-prop_year)/(yr_last-prop_year))*(c_hist.loc[yr_last]-c_hist.loc[prop_year]) + c_hist.loc[prop_year]

            #estimate CH4 based on proportionality
            uncond_lb = (cndc['Unconditional_LB']/pre_cndc) * pre_mndc
            uncond_ub = (cndc['Unconditional_UB']/pre_cndc) * pre_mndc
            cond_lb = (cndc['Conditional_LB']/pre_cndc) * pre_mndc
            cond_ub = (cndc['Conditional_UB']/pre_cndc) * pre_mndc

            data.loc[country] = [yr_near,\
                                 'CH4',\
                                 uncond_lb,\
                                 uncond_ub,\
                                 cond_lb,\
                                 cond_ub,\
                                 'Yes'
                                 ]

      return data


def gmp_ch4(data,ch4_hist,country_add_GMP=['EU27'],gmp_red=0.3):

      data_adj = data.copy()
      
      #add new countries to GMP list as per user
      add_to_GMP(country_add_GMP)

      for country in countries_GMP:
            
            if country in data.index:
                  #get the reference emission to implement GMP            
                  ref_emiss = ch4_hist.loc[country,2019]/1000

                  #calculate GMP compliant emission
                  gmp_emiss = ref_emiss*(1-gmp_red)

                  data_adj.loc[country,'Unconditional_LB'] = min(data.loc[country,'Unconditional_LB'],gmp_emiss)
                  data_adj.loc[country,'Unconditional_UB'] = min(data.loc[country,'Unconditional_UB'],gmp_emiss)
                  data_adj.loc[country,'Conditional_LB'] = min(data.loc[country,'Conditional_LB'],gmp_emiss)
                  data_adj.loc[country,'Conditional_UB'] = min(data.loc[country,'Conditional_UB'],gmp_emiss)

      return data_adj



            


      





      




  




#--END--
