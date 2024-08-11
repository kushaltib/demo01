import altair as alt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import streamlit as st


from model import mod_read_input, mod_nearterm_CO2eq, mod_longterm_CO2eq, mod_emissions_projection, mod_emissions_projection_method03,mod_CH4,mod_N2O
import streamlit_page01

def format_text(value):
    value = int(value)

    if value > 0:
        color = 'red'
    else:
        color = 'green'
    return f"<div style='color:{color}; font-size:20px; text-align: center;'><b>{value} GtCO2eq</b></div>"



st.title("NDC pledges for selected countries")


#@st.cache_data

with st.sidebar:
    
    if st.checkbox('show plot'):
        show=0
    else:
        show=1
        
    #---inventory
    selected_inventory= st.selectbox("Historical Inventory:",['PRIMAPv5','EDGARv6'])
    hist_co2eq_excl = mod_read_input.read_hist(selected_inventory,'CO2eq','excl') #read historical emissions data
    hist_co2_excl = mod_read_input.read_hist(selected_inventory,'CO2','excl') #read historical emissions data
    hist_ch4 = mod_read_input.read_hist('PRIMAPv5','CH4','net')
    hist_n2o = mod_read_input.read_hist('PRIMAPv5','N2O','net')

    #--land-use data source
    selected_luc = st.selectbox("Land-use data:",['OSCAR+DGVM','NGHGI'])
    if selected_luc=='OSCAR+DGVM':
        hist_luc_emiss = mod_read_input.read_luc('emiss','OSCAR')
        hist_luc_sink = mod_read_input.read_luc('sink','Grassi')
        hist_luc_net = hist_luc_sink+hist_luc_emiss
    
    if selected_luc=='NGHGI':
        hist_luc_net = mod_read_input.read_luc('net','NGHGI')

    #--GDP
    gdp = mod_read_input.read_gdp()


    #read and process NDC data:
    NDC = mod_read_input.read_ndc()
    #near-term parameters
    co2eq, co2eq_excl,co2eq_luc = mod_nearterm_CO2eq.create_ndc_table(NDC,hist_luc_net,hist_co2_excl,hist_co2eq_excl,gdp)

    #---country
    #selected_country= st.selectbox("Choose Country:",NDC.index)
    selected_country= st.selectbox("Country:",sorted(co2eq_excl.index[co2eq_excl['Processed']=='Yes']))

    #--years for the display plot
    start, end = st.slider("Range of years", 
                           min_value=1850,
                           max_value=2100,
                           value=(1985, 2100),        
                           step=1
                          )
    

    #--fitting method
    selected_fitmethod = st.selectbox("Fitting method",['Olivier old','Olivier revised'])
    #selected_fitmethod = st.selectbox("Fitting method",['Olivier revised'])
    
    
    #--allowance limit of negative emissions
    eneg = st.slider(label="Allow neg emission (rel. to present emissions)",
                     min_value=10,
                     max_value=100,
                     value=10,
                     step=10,
                     #key='slider3'
                     )
    
    
    #--limit of minimum value of growth rate
    #gmax = st.slider(label="Annual growth rate (%)",
    #                 min_value=10,
    #                 max_value=40,
    #                 value=10,
    #                 step=1,
    #                 #key='slider3'
    #                 )
    gmax=10

    #--controlling the change in growth rate
    #dg = st.slider(label="Annual change in growth rate (%)",
    #                 min_value=2,
    #                 max_value=6,
    #                 value=2,
    #                 step=1,
    #                 #key='slider3'
    #                 )
    dg=2


    #--parameters relevant for the Olivier's method:
    if st.checkbox('Remove quardractic correction'):
        corr=0
    else:
        corr=1

    if st.checkbox('Do not overwrite asymptotic emissions with net-zero pledge'):
        asm=0
    else:
        asm=1

#st.markdown("<hr>", unsafe_allow_html=True)


#more ndc and long term parameters:
ch4_summ = mod_CH4.def_ch4(NDC,co2eq_excl,hist_ch4,hist_co2_excl,hist_co2eq_excl)

n2o_summ = mod_N2O.def_n2o(NDC,co2eq_excl,hist_n2o)


#co2eq_nz = mod_longterm_CO2eq.grp_nz(NDC,process='co2eq')
co2eq_nz = mod_longterm_CO2eq.co2_nz(NDC,ch4_summ,n2o_summ)

ehist = hist_co2_excl.loc[selected_country]
endc = co2eq_excl.loc[selected_country]
enz = co2eq_nz.loc[selected_country]
ndc_ch4 = ch4_summ.loc[selected_country]
ndc_n2o = n2o_summ.loc[selected_country]

#--base trajectory
if selected_fitmethod=='Olivier old':
    #----Olivier's method
    emiss_coun = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,gmax=gmax/100,dg0=dg/100,corr=corr,asm=asm)

if selected_fitmethod=='Olivier revised':
    #----New method
    emiss_coun = mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o)

#--for comparing to old version in the paper:
paper = pd.read_excel("./data/comparing/paper_co2_nogmp.xlsx",index_col=0)
emiss_paper = paper.loc[selected_country]


if show==1:
    streamlit_page01.page01(selected_fitmethod,selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg,gmax,dg,asm,corr,emiss_coun,hist_co2eq_excl,emiss_paper,co2eq_excl,NDC,hist_luc_net,start,end)