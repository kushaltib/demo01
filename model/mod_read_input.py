# -*- coding: utf-8 -*-

#--import python packages
import warnings
import sys
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from scipy.optimize import minimize, curve_fit, OptimizeWarning
import pathlib
import argparse
#

#--keep the warnings silent
warnings.simplefilter("ignore", OptimizeWarning)

def read_ndc():
    
    #--read the NDC file
    NDC = pd.read_excel("./data/Approach_v2_June2024/NDCdata_As12Jun2024_Upd29Jul2024_v2.xlsx")
    NDC.drop(columns=['Categories'],inplace=True)
    NDC = NDC.T
    header_col = NDC.iloc[0]
    NDC = NDC[1:]
    NDC.columns = header_col

    return NDC

def read_hist(inventory_name,pollutant,sector):

    #--read the inventory file
    data = pd.read_excel("./data/hist_data/"+inventory_name+"_"+pollutant+"_"+sector+".xlsx")
    data.set_index('Name',inplace=True)

    return data

def read_luc(flux_type,data_source):

    #--read the LULUCF file
    data = pd.read_excel("./data/hist_data/LUC_"+flux_type+"_"+data_source+".xlsx")
    data.set_index('Name',inplace=True)

    return data
    
def read_gdp(ssp=0):

    if ssp==0:
        ssp1 = pd.read_excel("./data/hist_data/GDP_SSP1.xlsx",index_col=0)
        ssp2 = pd.read_excel("./data/hist_data/GDP_SSP2.xlsx",index_col=0)
        ssp3 = pd.read_excel("./data/hist_data/GDP_SSP3.xlsx",index_col=0)
        ssp4 = pd.read_excel("./data/hist_data/GDP_SSP4.xlsx",index_col=0)
        ssp5 = pd.read_excel("./data/hist_data/GDP_SSP5.xlsx",index_col=0)

        gdp = (ssp1+ssp2+ssp3+ssp4+ssp5)/5.

    elif ssp==1:
        gdp = pd.read_excel("./data/hist_data/GDP_SSP1.xlsx",index_col=0)
    
    elif ssp==2:
        gdp = pd.read_excel("./data/hist_data/GDP_SSP2.xlsx",index_col=0)
    
    elif ssp==3:
        gdp = pd.read_excel("./data/hist_data/GDP_SSP3.xlsx",index_col=0)
    
    elif ssp==4:
        gdp = pd.read_excel("./data/hist_data/GDP_SSP4.xlsx",index_col=0)
    
    elif ssp==5:
        gdp = pd.read_excel("./data/hist_data/GDP_SSP5.xlsx",index_col=0)

    
    #merge with the historical gdp:
    gdp_his = pd.read_excel("./data/hist_data/GDP_his.xlsx",index_col=0)
    merge_gdp = pd.merge(gdp_his.loc[:, gdp_his.columns < 2010],gdp,left_index=True,right_index=True)

    
    return merge_gdp



    #average of all ssps if 0



#--END--
