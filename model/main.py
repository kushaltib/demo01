# -*- coding: utf-8 -*-

#the main file for creating country-level future projections

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


#--import modules
import mod_read_input
import mod_CO2eq_future








#--run the model:





#0--gather the input data

#--NDC table
NDC = mod_read_input.read_ndc()

#--historical emissions
co2eq_excl = mod_read_input.read_hist('PRIMAPv5','CO2eq','excl')
co2_excl = mod_read_input.read_hist('PRIMAPv5','CO2eq','excl')
ch4_net = mod_read_input.read_hist('PRIMAPv5','CO2eq','excl')
n2o_net = mod_read_input.read_hist('PRIMAPv5','CO2eq','excl')

#--co2 emissions from land-use sector
luc_emiss = mod_read_input.read_luc('emiss','OSCAR')
luc_sink = mod_read_input.read_luc('sink','Grassi')
luc_net = luc_emiss+luc_sink
luc_net_nghgi = mod_read_input.read_luc('net','NGHGI')



#1--collect scenario configuration

#2--estimate CO2eq for future time stamps
mod_CO2eq_future.process_ndc(NDC)

#3--estimate non-CO2 timeline

#4--estimate LULUCF timeline

#5--estimate CO2 timeline

#6--estimate CO2eq timeline


#7--estimate TCRE dT









#--keep the warnings silent
warnings.simplefilter("ignore", OptimizeWarning)






#--END--
