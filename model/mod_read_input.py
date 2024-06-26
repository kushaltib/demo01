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
    NDC = pd.read_excel("./data/NDCdata_As12Jun2024_Upd12Jun2024_v2.xlsx")
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
    



#--END--
