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

#--find first value smaller than x0 in a list
def first_neg(lst,x0):
    res = [i for i,x in enumerate(lst) if x < x0]
    return None if res == [] else res[0]


#--quadratic function of x 
#--input x is either a float or a numpy array, a,b,c are constants
def ax2bxc(x,a,b,c):
    return a*x*x+b*x+c


#--function to compute emissions using the simple model by --Edwards et al, Environmental Science & Policy, 66, 191-198, 2016
#---- doi: 10.1016/j.envsci.2016.08.013

#---- E0: emission at initial year
#---- g0: growth rate of emissions at initial year
#---- Eneg: asymptotic emissions (can be negative but does not have to be)
#---- dg: yearly increment in growth rate

def emi_calc(E0,g0,Eneg,dg,year_start=2023,gmax=0.1):
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
        #g=max(g,-gmax)
        #--growth rate is appended to list
        g_list.append(g)
    #--return list of emissions
    return emi_list
#



#--cost function to compute mismatch to our targets
#---- x: control vector (g0, Eneg, dg)
#---- E0: emission at initial year
#---- gi0: a priori value of growth rate at initial year
#---- Enear: emission target for yr_near
#---- Elong: emission target for yr_long (e.g. 0 if neutrality)
#---- yr_last: latest year for which inventory is available
#---- yr_near: target year for near-term target
#---- yr_long: target year for long-term target



def cost(x,E0,gi0,Enear,Elong,yr_last,yr_near,yr_long):

    #--decomposing control vector
    g0=x[0]          #--growth rate in 2018 (can be optimised)
    Eneg=x[1]+Elong  #--asymptotic emissions
    dg=x[2]          #--change in growth rate year on year
    
    #--compute emission time profile
    emi_list=emi_calc(E0=E0,g0=g0,Eneg=Eneg,dg=dg)

    #--compute simulated year for long-term target
    if first_neg(emi_list,Elong) != None:
        yr_long_simulated=yr_last+first_neg(emi_list,Elong)
    else:
        yr_long_simulated=yr_last
    
    #--compute cost function as departure from g0, near-term target, long-term target and long-term target year
    #--each term of the cost function is weighted by a reasonable value
    err= 100.*((emi_list[yr_near-yr_last]-Enear)/E0)**2 + \
         5.*((emi_list[yr_long-yr_last]-Elong)/E0)**2. + \
         10.*((yr_long_simulated-yr_long)/10.)**2. + \
         ((g0-gi0)/gi0)**2.
    
    return err



def create_timeseries(country,emiss_hist,emiss_ndc,emiss_nz,gmax=0.1,dg0=0.02,eneg=10,corr=1,asm=1,duncond=1,dcond=1,dndcyr=0,dnzyr=0):
     
     E0=emiss_hist.values[-1]  #-- emissions at t=0
     yr_last = emiss_hist.index[-1] 
     
     #--developing initial control vector for the minimation

     #----g0: initial growth rate
     #--perform fit to diganose a priori initial rate of emission by using last 5 years of hist emissions
     X_yr = np.array(emiss_hist.index[-5:]).reshape(-1, 1)
     Y_emiss = emiss_hist.values[-5:].reshape(-1, 1)
     model = LinearRegression().fit(X_yr,Y_emiss)
     
     Ep0=model.coef_[0]                    #--rate of emissions change at t=0
     g0=Ep0/E0                #--rate of emissions change (as a fraction)
     
     #----dg: annual change in growth rate
     dg=dg0

     #----Eneg0:

     #--Maximum asymptotic negative emissions in 2100 (ktCO2/yr)
     if E0<0: Eneg_max=E0*1.1
     else: Eneg_max=-E0/eneg
     
     Eneg0 = Eneg_max/2.

     x0=[g0,Eneg0,dg]
     x0 = np.array(x0, dtype=object)



     #
     
     #--define bounds for minimation of control vector x
     #---- g0 +/- dg0: on initial growth rate
     #---- Eneg_max to 0 for asymptotic negative emissions
     #---- 0 to gmax for initial increment in growth rate

     bnds = ([g0-dg0,g0+dg0],[Eneg_max,0.0],[0,gmax])
     #

     #--getting the near-term and long-term parameters:
     yr_near = emiss_ndc['Year']+dndcyr
     emiss_near = emiss_ndc[['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB']].values.tolist()
     dnear=[duncond,duncond,dcond,dcond]
     yr_nz = emiss_nz['Year']+dnzyr
     Elong = emiss_nz['co2eq_excl']


     #--initialize empty dataframe to store projected timeseries:
     emiss_proj=pd.DataFrame(0.0,index=['Unconditional_LB','Unconditional_UB','Conditional_LB','Conditional_UB'],columns=range(yr_last,2101))

     if emiss_nz['Neutrality']=='Yes':
          
          for i in range(4):
               
               #convert the emissions into kT/year
               Enear=emiss_near[i]*1000

               #adjust for user specificed changes to NDC targets
               Enear=Enear*dnear[i]

               #--adjust Elong if 2030 value is lower
               if Enear<Elong: Elong=Enear

               #--low ambition: emission trajectory minimization with x0 as initial conditions and bnds bounds
               #cost(x,E0,gi0,Enear,Elong,yr_last,yr_near,yr_long)
               #cost(x,E0,gi0,E2030,Elong,yr_long)
               res = minimize(cost, x0, args=(E0,g0,Enear,Elong,yr_last,yr_near,yr_nz), bounds=bnds, method='SLSQP')
               
               #--flag to detect if minimisation algorithm has converged
               emi_success=res['success']
               #--populate Scen_CO2_low based on the neutrality pathway
               if emi_success:
                    #--x control vector after optimisation
                    x=res['x']
                    #--recompute CO2 emission trajectory for vector x
                    
                    emi_list=np.array(emi_calc(E0,x[0],x[1]+Elong,x[2],year_start=yr_last+1))
                    #--make a quadratic fit to correct for the error term
                    #--the quadratic function is 0 for the 3 points defined by years "year last",2030,yr_neutrality
                    abc,cov=curve_fit(ax2bxc, [yr_last,yr_near,yr_nz], [0.0,Enear-emi_list[yr_near-yr_last],Elong-emi_list[yr_nz-yr_last]])
                    #--reconstruct the CO2 emission trajectory
                    #--initialise with recomputed emi_list
                    emiss_proj.iloc[i]=emi_list  #np.append([E0*(1-g0)],emi_list)
                    #--add correction term for the period: "year last" to "long-term target year"
                    if corr==1: emiss_proj.iloc[i][np.arange(yr_last,yr_nz+1)] += ax2bxc(np.arange(yr_last,yr_nz+1),*abc)
                    #--overwrite Elong value beyond long-term target year
                    if asm==1: emiss_proj.iloc[i][np.arange(yr_nz+1,2101)]=Elong
                                   
               else:
                    print(country,': neutrality low optimisation did not converge')


     return emiss_proj           

#--END--


