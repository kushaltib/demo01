# -*- coding: utf-8 -*-

#--import python packages
import re
import warnings
import sys
import pandas as pd
import numpy as np
import math
import matplotlib as mpl
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.optimize import minimize, curve_fit, OptimizeWarning, fsolve
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

#--find first value smaller than x0 in a list
def first_neg(lst,x0):
    res = [i for i,x in enumerate(lst) if x < x0]
    return None if res == [] else res[0]


#--function to compute emissions using the simple model by --Edwards et al, Environmental Science & Policy, 66, 191-198, 2016
#---- doi: 10.1016/j.envsci.2016.08.013

#---- E0: emission at initial year
#---- g0: growth rate of emissions at initial year
#---- Eneg: asymptotic emissions (can be negative but does not have to be)
#---- dg: yearly increment in growth rate

def emi_calc(E0,g0,Eneg,dg_near,dg_long,year_start=2023,year_ndc=2030,year_end=2100,country=None):
    #--initialising to latest-year values
    emi_list=[E0]  #--list of yearly emission values
    g=g0           #--growth rate
    g_list=[g]     #--list of yearly g values

    #--loop on years "year_start" to "year_end"
    for yr in range(year_start,year_end+1):
        
        g = np.round(g,5)

        emi=Eneg+(E0-Eneg)*np.exp(np.sum(np.array(g_list,dtype=object)))

        #--print
        #print(yr,"---",g,"---",np.sum(np.array(g_list,dtype=object)),"---",emi)
        
        if yr<year_ndc:
             #--growth rate is reduced linearly
             g=g-dg_near

             if yr==year_ndc-1 and country=="Int. Aviation":
                  g=0

        else:
             #--growth rate is reduced linearly
             g=g-dg_long
                            
        #--emission is appended to list
        emi_list.append(emi)
        
        
        
        #--growth rate is appended to list
        g_list.append(g)

        

    
    #--return list of emissions
    return emi_list#,g_list


#--constraint-01:
def em_nr(dg_near,E0,g0,Enear,Elong,yr_last,yr_near,country=None):
     
     #--compute emission time profile up to NDC year
     emi_list=emi_calc(E0,g0,Elong,dg_near,0.002,yr_last+1,yr_near,yr_near,country)

     #--compute difference between the modeled NDC emissions and actual target 
     cons1=(emi_list[yr_near-yr_last]-Enear)

     #--return the absolute value of the difference - i.e. without the sign    
     return abs(cons1)

#--constraint-02:
def em_lg(dg_long,dg_near,E0,g0,Elong,yr_last,yr_near,yr_long,country=None):
     
     #--compute emission time profile
     emi_list=emi_calc(E0,g0,Elong,dg_near,dg_long,yr_last+1,yr_near,country=country)

     #--compute the 0.X% emissions
     emi_pntXper = Elong + (0.005*(E0-Elong))

     #--modelled emissions at NZ year
     emi_nz_mod = emi_list[yr_long-yr_last] 

     #--compute constraint 
     cons2 = emi_pntXper-emi_nz_mod
         
     return abs(cons2)
          

     
     

def create_timeseries_equ(country,emiss_hist,emiss_ndc,emiss_nz,ndc_ch4,ndc_n2o,gmax=0.1,dg0=0.02):
     
     E0=emiss_hist.values[-1]  #-- emissions at t=0
     yr_last = emiss_hist.index[-1] 
     
     #----g0: initial growth rate
     
     #--perform fit to diganose a priori initial rate of emission by using last 5 years but skipping 2020 of hist emissions
     
     #set index to just skip 2020 for whatever may be the last-year of inventory
     ind_2020 = len(emiss_hist.index.tolist()) - emiss_hist.index.tolist().index(2020)
     
     if ind_2020>5:
          X_yr = np.array(emiss_hist.index[-5:]).reshape(-1, 1)
          Y_emiss = emiss_hist.values[-5:].reshape(-1, 1)
     else:
          X_yr = np.array(emiss_hist.index[-6:][:-ind_2020].tolist()+emiss_hist.index[-6:][-ind_2020+1:].tolist()).reshape(-1, 1)
          Y_emiss = np.array(emiss_hist.values[-6:][:-ind_2020].tolist()+emiss_hist.values[-6:][-ind_2020+1:].tolist()).reshape(-1, 1)

     model = LinearRegression().fit(X_yr,Y_emiss)
     
     Ep0=model.coef_[0]                    #--rate of emissions change at t=0
     g0=Ep0/E0                #--rate of emissions change (as a fraction)
     

     
     #--getting the near-term parameters:
     yr_near = emiss_ndc['Year']
     emiss_near = emiss_ndc[['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB']].values.tolist()
     
     
     emiss_ch4 = ndc_ch4[['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB']].values.tolist()
     emiss_n2o = ndc_n2o[['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB']].values.tolist()

     
     #--getting long-term parameters:
     yr_nz = emiss_nz['Year']
     if yr_nz>2100: yr_nz=2100

     emiss_long = emiss_nz[['CO2_nz_uncond_lb','CO2_nz_uncond_ub','CO2_nz_cond_lb','CO2_nz_cond_ub']].values.tolist()
     #Elong = emiss_nz['co2eq_excl']+0.001
     #Elong = emiss_nz['co2eq_excl']-(0.05*E0)


     #--initialize empty dataframe to store projected timeseries:
     emiss_proj=pd.DataFrame(0.0,index=['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB'],columns=range(yr_last,2101))
     x_res = pd.DataFrame(0.0,index=['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB'],columns=['near','long'])
     ndc_shift = pd.DataFrame(0.0,index=['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB'],columns=['Year','Value'])

     for i in range(4):
          
          #Convert to CO2 emissions if NDC has CO2eq:
          if emiss_ndc['Applies']=='CO2eq':
               Enear = emiss_near[i]-(emiss_ch4[i]*28)-(emiss_n2o[i]*265)
          else:
               Enear=emiss_near[i]
          
                         
          #convert the emissions into kT/year
          Enear=Enear*1000

          #CO2 for net-zero:
          Elong = emiss_long[i]*1000
               
          #--adjust Elong if 2030 value is lower
          if Enear<Elong: Elong=Enear

          #--set Elong 0 for non nz countries:
          if emiss_nz['Neutrality'] !='Yes': Elong=0


          #initial guesses
          dg_near=0.00
          dg_long=0.00
               
          #first fix dg_near:
          solution_near = fsolve(em_nr, dg_near, args=(E0,g0,Enear,Elong,yr_last,yr_near,country))

          #--flag to detect if minimisation algorithm has converged
          near_success=True

          #--sto ndc info:
          #ndc_shift.iloc[i]=[yr_near,Enear]

          if near_success:
               
               dg_near = solution_near[0]#['x']

               if emiss_nz['Neutrality']=='Yes' or emiss_nz['Neutrality']=='Other':
                    #second fix dg_long:
                    solution_long = fsolve(em_lg, dg_long, args=(dg_near,E0,g0,Elong,yr_last,yr_near,yr_nz,country))

                    #--flag to detect if minimisation algorithm has converged
                    long_success=True

                    if long_success:
                         dg_long = solution_long[0]#['x']

                         #--recompute CO2 emission trajectory for vector x
                         emi_list=np.array(emi_calc(E0,g0,Elong,dg_near,dg_long,yr_last+1,yr_near,country=country))

                         #--replace with recomputed emi_list
                         emiss_proj.iloc[i]=emi_list

               else:

                    emi_list = np.array(emi_calc(E0,g0,Elong,dg_near,dg_long,yr_last+1,yr_near,yr_near,country=country))
                    emiss_proj.iloc[i,0:yr_near-yr_last+1] = emi_list#+emi_list[yr_near-yr_last]*(2100-yr_near)
                    emiss_proj.iloc[i,yr_near-yr_last+1:] = Enear

                   
               #--store optimization results
               #x_res.iloc[i]=[dg_near,dg_long]
                         

               #--print info:
               #print(country,' ',emiss_proj.index[i],': converged')

                                   
          #else:
               #print(country,' ',emiss_proj.index[i],':did not converge')
     

     print(country)

     return emiss_proj#,x_res,ndc_shift,E0,g0


#the function takes one country info at a time and projects timeline
#linearly from last-year to ndc-year and then constant upto end-year

def create_timeseries_near(country,emiss_ndc,emiss_hist):
      
      #lst year inventory information:
      yr_last = emiss_hist.index[-1]
      emiss_last = emiss_hist.values[-1]
      

      yr_near = emiss_ndc['Year']
      emiss_near = emiss_ndc[['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB']].values.tolist()

      #--initialize empty dataframe to store projected timeseries:
      emiss_proj=pd.DataFrame(0.0,index=['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB'],columns=range(yr_last,2101))

      for i in range(4):
               
               #initiate the time-series with emissions for last year
               emi_list=[emiss_last]

               #convert the ndc emissions into kT/year
               Enear=emiss_near[i]*1000

               #now linearly project from last-year to ndc-year
               for yr in range(yr_last+1,2101):
                     
                     if yr<yr_near:
                           emi = ((yr-yr_last)*((Enear-emiss_last)/(yr_near-yr_last)))+emiss_last
                     elif yr==yr_near:
                           emi = Enear
                     else:
                           emi=Enear
                     
                     #--emission is appended to list
                     emi_list.append(emi)
               
               #--save the projection to the dataframe
               emiss_proj.iloc[i] = emi_list
     
      print(country+" done")
      
      return emiss_proj



def create_timeseries_notar(country,emiss_hist):

      #lst year inventory information:
      yr_last = emiss_hist.index[-1]
      emiss_last = emiss_hist.values[-1]

      #--initialize dataframe to store projected timeseries:
      emiss_proj=pd.DataFrame(emiss_last,index=['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB'],columns=range(yr_last,2101))


      print(country)
     
      return emiss_proj

                
           








#--END--


