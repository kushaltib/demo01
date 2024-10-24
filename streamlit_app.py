import altair as alt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import streamlit as st

from model import mod_read_input, mod_nearterm_CO2eq, mod_longterm_CO2eq, mod_emissions_projection, mod_emissions_projection_method03,mod_CH4,mod_N2O


def format_text(value):
    value = int(value)

    if value > 0:
        color = 'red'
    else:
        color = 'green'
    return f"<div style='color:{color}; font-size:20px; text-align: center;'><b>{value} GtCO2eq</b></div>"



st.title("GHG emissions projections based on National Climate pledges")

col1,col2=st.columns([0.3, 0.7])
with col1:
    #--choose gas
    selected_gas = st.selectbox("Choose gas:",['CO2eq','CO2','CH4','N2O'])

with col2:
    #--years for the display plot
    start, end = st.slider("Range of years", 
                        min_value=1850,
                        max_value=2100,
                        value=(1985, 2100),        
                        step=1
                        )



#@st.cache_data

with st.sidebar:
    
        
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

    #--inlcuding luc for net-zero
    if st.checkbox('Include LUC for net-zero'):
            incl_luc=1
    else:
            incl_luc=0

    #--GDP
    gdp = mod_read_input.read_gdp()

   
    #---country
    #read and process NDC data:
    NDC = mod_read_input.read_ndc()
    #selected_country= st.selectbox("Choose Country:",NDC.index)
    selected_country= st.selectbox("Country:",sorted(NDC.index),index=44)
    if st.checkbox('Show Global'):
            glob_tot=1
    else:
            glob_tot=0

    
       
    if glob_tot==1:
        selected_fitmethod = 'Revised'
        xper = 0.5
    

    if glob_tot==0:
        #--fitting method
        selected_fitmethod = st.selectbox("Fitting method",['Revised','Old'])
        #selected_fitmethod = st.selectbox("Fitting method",['Olivier revised'])

        #--parameters relevant for the REVISED method:
        if selected_fitmethod == 'Revised':
            xper = st.slider(label="Point X percent at net-zero year",
                             min_value=0.1,
                             max_value=3.0,
                             value=1.0,
                             step=0.1,
                             #key='slider3'
                             )
    
    
        #--parameters relevant for the OLD method:
        if selected_fitmethod == 'Old':
                #--set allowance limit of negative emissions
                eneg = st.slider(label="Allow neg emission (rel. to present emissions)",
                                 min_value=10,
                                max_value=100,
                                value=10,
                                step=10,
                                #key='slider3'
                                )
      
    
                if st.checkbox('Remove quardractic correction'):
                    corr=0
                else:
                    corr=1

                if st.checkbox('Do not overwrite asymptotic emissions with net-zero pledge'):
                    asm=0
                else:
                    asm=1


#st.markdown("<hr>", unsafe_allow_html=True)

#----------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------

#ndc and long term parameters for BASE scenario:
#tables for all country
co2eq, co2eq_excl,co2eq_luc = mod_nearterm_CO2eq.create_ndc_table(NDC,hist_luc_net,hist_co2_excl,hist_co2eq_excl,gdp)
ch4_summ = mod_CH4.def_ch4(NDC,co2eq_excl,hist_ch4,hist_co2_excl,hist_co2eq_excl)
n2o_summ = mod_N2O.def_n2o(NDC,co2eq_excl,hist_n2o)
co2eq_nz = mod_longterm_CO2eq.co2_nz(NDC,ch4_summ,n2o_summ,co2eq_luc,hist_co2_excl,hist_co2eq_excl,incl_luc=incl_luc)

ehist = hist_co2_excl.loc[selected_country]
endc = co2eq_excl.loc[selected_country]
enz = co2eq_nz.loc[selected_country]
ndc_ch4 = ch4_summ.loc[selected_country]
ndc_n2o = n2o_summ.loc[selected_country]


#for countries with target
if endc['Processed']=='Yes':

    #--base trajectory
    
    #calculate CO2 trajectory:
    if selected_fitmethod=='Old':
        #----Olivier's method
        emiss_co2_excl = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,corr=corr,asm=asm)

    if selected_fitmethod=='Revised':
        #----New method
        emiss_co2_excl = mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,xper)

    #calculate CH4 and N2O:
    emiss_ch4 = mod_emissions_projection_method03.create_timeseries_near(selected_country,ndc_ch4,hist_ch4.loc[selected_country])
    emiss_n2o = mod_emissions_projection_method03.create_timeseries_near(selected_country,ndc_n2o,hist_n2o.loc[selected_country])


#--for non target countries:
else:
    emiss_co2_excl = mod_emissions_projection_method03.create_timeseries_notar(selected_country,ehist)
    emiss_ch4 = mod_emissions_projection_method03.create_timeseries_notar(selected_country,hist_ch4.loc[selected_country])
    emiss_n2o = mod_emissions_projection_method03.create_timeseries_notar(selected_country,hist_n2o.loc[selected_country])


if selected_country in ["Int. Shipping","Int. Aviation"]:
    emiss_luc = 0
else:
    emiss_luc = mod_emissions_projection_method03.create_timeseries_near(selected_country,co2eq_luc.loc[selected_country],hist_luc_net.loc[selected_country]) 

#calculate CO2eq:
emiss_co2eq_excl = emiss_co2_excl+28*emiss_ch4+265*emiss_n2o
emiss_co2eq_net = emiss_co2eq_excl+emiss_luc

#--for comparing to old version in the paper:
paper_co2_uncond = pd.read_excel("./data/precalculated/paper_co2_nogmp_uncond.xlsx",index_col=0)
emiss_paper_co2_uncond = paper_co2_uncond.loc[selected_country]
emiss_paper_glob_tot_co2_uncond = paper_co2_uncond.sum()

paper_co2_cond = pd.read_excel("./data/precalculated/paper_co2_nogmp_cond.xlsx",index_col=0)
emiss_paper_co2_cond = paper_co2_cond.loc[selected_country]
emiss_paper_glob_tot_co2_cond = paper_co2_cond.sum()


paper_co2eq_uncond = pd.read_excel("./data/precalculated/paper_co2eq_nogmp_uncond.xlsx",index_col=0)
emiss_paper_co2eq_uncond = paper_co2eq_uncond.loc[selected_country]
emiss_paper_glob_tot_co2eq_uncond = paper_co2eq_uncond.sum()

paper_co2eq_cond = pd.read_excel("./data/precalculated/paper_co2eq_nogmp_cond.xlsx",index_col=0)
emiss_paper_co2eq_cond = paper_co2eq_cond.loc[selected_country]
emiss_paper_glob_tot_co2eq_cond = paper_co2eq_cond.sum()


#--for global data:
revised_glob_tot_co2_uncond = pd.read_excel("./data/precalculated/CO2_excl_bycountry_revisedmethod_uncond.xlsx",index_col=0)
emiss_revised_glob_tot_co2_uncond = revised_glob_tot_co2_uncond.sum()

revised_glob_tot_co2_cond = pd.read_excel("./data/precalculated/CO2_excl_bycountry_revisedmethod_cond.xlsx",index_col=0)
emiss_revised_glob_tot_co2_cond = revised_glob_tot_co2_cond.sum()

revised_glob_tot_co2eq_uncond = pd.read_excel("./data/precalculated/CO2eq_excl_bycountry_revisedmethod_uncond.xlsx",index_col=0)
emiss_revised_glob_tot_co2eq_uncond = revised_glob_tot_co2eq_uncond.sum()

revised_glob_tot_co2eq_cond = pd.read_excel("./data/precalculated/CO2eq_excl_bycountry_revisedmethod_cond.xlsx",index_col=0)
emiss_revised_glob_tot_co2eq_cond = revised_glob_tot_co2eq_cond.sum()

pnt2_co2eq = pd.read_excel("./data/precalculated/BASEpnt2_WORLD_CO2eq_excl.xlsx",index_col=0)
pnt2_co2 = pd.read_excel("./data/precalculated/BASEpnt2_WORLD_CO2_excl.xlsx",index_col=0)
pnt5_co2eq = pd.read_excel("./data/precalculated/BASEpnt5_WORLD_CO2eq_excl.xlsx",index_col=0)
pnt5_co2 = pd.read_excel("./data/precalculated/BASEpnt5_WORLD_CO2_excl.xlsx",index_col=0)
c1_co2eq = pd.read_excel("./data/precalculated/BASE1_WORLD_CO2eq_excl.xlsx",index_col=0)
c1_co2 = pd.read_excel("./data/precalculated/BASE1_WORLD_CO2_excl.xlsx",index_col=0)
c2_co2eq = pd.read_excel("./data/precalculated/BASE2_WORLD_CO2eq_excl.xlsx",index_col=0)
c2_co2 = pd.read_excel("./data/precalculated/BASE2_WORLD_CO2_excl.xlsx",index_col=0)
c3_co2eq = pd.read_excel("./data/precalculated/BASE3_WORLD_CO2eq_excl.xlsx",index_col=0)
c3_co2 = pd.read_excel("./data/precalculated/BASE3_WORLD_CO2_excl.xlsx",index_col=0)




#----------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------

# #--controlling shifts in NDC levels, NDC year and NZ year
# col1,col2=st.columns(2)

# with col1: 
#     st.markdown(f"<div style='text-align: center;'>Adjust emissions w.r.t. declared targets<br>(<b>>1</b> = more emissions) </div>",
#                 unsafe_allow_html=True)
    
# with col2:
#     st.markdown(f"<div style='text-align: center;'>Adjust year w.r.t declared targets<br> (<b>>0</b> = delay it further) </div>",
#                 unsafe_allow_html=True)
    

# col1,col2,col3,col4=st.columns(4)

# default=[1.0,1.0,0,0]

# with col1:
#     duncond= st.slider(label="Uncond. emissions",
#                        min_value=0.7,
#                        max_value=1.3,
#                        value=default[0],
#                        step=0.05,
#                        #key='slider1'
#                        )

# with col2:
#     dcond= st.slider(label="Cond. emissions",
#                      min_value=0.7,
#                      max_value=1.3,
#                      value=default[1],
#                      step=0.05,
#                      #key='slider2'
#                     )

# with col3:
#     dndcyr= st.slider(label="NDC year",
#                       min_value=0,
#                       max_value=10,
#                       value=default[2],
#                       step=1,
#                       #key='slider3'
#                       )

# with col4:
#     dnzyr= st.slider(label="Net-zero year",
#                      min_value=-10,
#                      max_value=10,
#                      value=default[3],
#                      step=1,
#                      #key='slider4'
#                      )


#--------------------------------------------------------------------------------------------
#--adjusted enhanced/delayed trajectories
# if selected_fitmethod=='Old':
#     #----Olivier's method
#     emiss_uncond= mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,corr=corr,asm=asm)
#     emiss_cond = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,corr=corr,asm=asm)
#     emiss_ndcyr = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,corr=corr,asm=asm)
#     emiss_nzyr = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,corr=corr,asm=asm)
#     emiss_allchg = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,corr=corr,asm=asm)

# if selected_fitmethod=='Revised':
#     #----New method
#     emiss_uncond= mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o)
#     emiss_cond = mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o)
#     emiss_ndcyr = mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o)
#     emiss_nzyr = mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o)



# #show the change in cumm. CO2eq with each type of change
# #for net-zero year
# i= 1 if dnzyr>0 else 0
# cumm_nzyr = emiss_nzyr.iloc[i].sum()/1000000 -emiss_coun.iloc[i].sum()/1000000


# #for ndc unconditional
# i=1 if duncond>1 else 0
# cumm_uncond = emiss_uncond.iloc[i].sum()/1000000 - emiss_coun.iloc[i].sum()/1000000

# #for ndc conditional
# i=3 if dcond>1 else 2
# cumm_cond = emiss_cond.iloc[i].sum()/1000000 - emiss_coun.iloc[i].sum()/1000000

# #for ndc year
# i= 1 if dndcyr>0 else 0
# cumm_ndcyr = emiss_ndcyr.iloc[i].sum()/1000000 - emiss_coun.iloc[i].sum()/1000000




# sentence = (
#     "Cumulative emissions "
#     "<b style='color: green;'>avoided</b> or "
#     "<b style='color: red;'>added</b>"
#     " for each type of change."
# )

# # Display the sentence
# st.markdown(sentence, unsafe_allow_html=True)


# col1,col2,col3,col4=st.columns(4)

# with col1:
#     st.markdown(format_text(cumm_uncond), unsafe_allow_html=True)

# with col2:
#     st.markdown(format_text(cumm_cond), unsafe_allow_html=True)

# with col3:
#     st.markdown(format_text(cumm_ndcyr), unsafe_allow_html=True)

# with col4:
#     st.markdown(format_text(cumm_nzyr), unsafe_allow_html=True)

if glob_tot==0:
    pnt2=0
    pnt5=0
    c1=0
    c2=0
    c3=0
    
if glob_tot==1:
    col1,col2,col3,col4=st.columns(4)

    with col1:
        if st.checkbox('0.2%'):
            pnt2=1
        else:
            pnt2=0

    with col2:
        if st.checkbox('0.5%'):
            pnt5=1
        else:
            pnt5=0

    with col3:
        if st.checkbox('1%'):
            c1=1
        else:
            c1=0
    
    #with col4:
    #    if st.checkbox('2%'):
    #        c2=1
    #    else:
    #        c2=0

    with col4:
        if st.checkbox('3%'):
            c3=1
        else:
            c3=0




    
#--horizontal line
#st.markdown("<hr>", unsafe_allow_html=True)



#display country plot
fig, ax = plt.subplots()

ax.set_title(selected_country,fontfamily="Arial",fontsize=10)

if selected_gas=='CO2eq':

    #lines:
    ax.plot(hist_co2eq_excl.loc[selected_country].index,
            hist_co2eq_excl.loc[selected_country].values/1000,
            '-', color='black',alpha=1, lw=2, label='CO2eq historical',mec='k',mew=0.5,ms=6
            )

    ax.plot(emiss_co2eq_excl.iloc[2].index,
            emiss_co2eq_excl.iloc[2].values/1000,
            'o-', color='violet',alpha=1, lw=2, label='Cond LB',mec='purple',mew=0.5,ms=3
            )

    ax.plot(emiss_co2eq_excl.iloc[3].index,
            emiss_co2eq_excl.iloc[3].values/1000,
            'o-', color='violet',alpha=1, lw=2, label='Cond UB',mec='purple',mew=0.5,ms=3
            )


    ax.plot(emiss_co2eq_excl.iloc[0].index,
            emiss_co2eq_excl.iloc[0].values/1000,
            'o-', color='grey',alpha=1, lw=2, label='UnCond LB',mec='purple',mew=0.5,ms=3
            )

    ax.plot(emiss_co2eq_excl.iloc[1].index,
            emiss_co2eq_excl.iloc[1].values/1000,
            'o-', color='grey',alpha=1, lw=2, label='UnCond UB',mec='purple',mew=0.5,ms=3
            )
    
    ax.plot(emiss_paper_co2eq_uncond.index,
            emiss_paper_co2eq_uncond.values/1000,
            ':', color='lightgrey',alpha=1, lw=2, label='Uncond',mec='k',mew=0.5,ms=3
            )
    
    ax.plot(emiss_paper_co2eq_cond.index,
            emiss_paper_co2eq_cond.values/1000,
            ':', color='pink',alpha=1, lw=2, label='Cond',mec='k',mew=0.5,ms=3
            )
    
    #plot net emissions:
    # if selected_country not in ['Int. Aviation','Int. Shipping']:
        
    #     data_len = min(len(hist_co2eq_excl.loc[selected_country].values),len(hist_luc_net.loc[selected_country].values))

    #     ax.plot(hist_luc_net.loc[selected_country].index[-data_len:],
    #             hist_co2eq_excl.loc[selected_country].values[-data_len:]/1000+hist_luc_net.loc[selected_country].values[-data_len:]/1000,
    #             '--', color='orange',alpha=1, lw=2, label='CO2eq historical net',mec='k',mew=0.5,ms=6
    #             )
        
    #     ax.plot(emiss_co2eq_net.iloc[0].index,
    #             emiss_co2eq_net.iloc[0].values/1000,
    #             'o-', color='grey',alpha=1, lw=2, label='UnCond LB',mec='purple',mew=0.5,ms=3
    #             )

    #plot base year values from NDC
    #plt.scatter(NDC.loc[selected_country,'Base_year'],
    #            NDC.loc[selected_country,'Base_CO2eq_emissions_Total-net'],
    #            label='Base net CO2eq',color='red',marker='o',edgecolors='orange',linewidths=1.5,s=40,zorder=20)

    plt.scatter(NDC.loc[selected_country,'Base_year'],
                NDC.loc[selected_country,'Base_CO2eq_emissions_Total-excl'],
                label='Base excl CO2eq',color='grey',marker='o',edgecolors='black',linewidths=2,s=40,zorder=20)
    
    
    

    #plot luc emissions:
    if selected_country not in ['Int. Aviation','Int. Shipping']:
        ax.plot(hist_luc_net.loc[selected_country].index,
                hist_luc_net.loc[selected_country].values/1000,
                '-', color='yellowgreen',alpha=1, lw=2, label='CO2eq historical luc net',mec='k',mew=0.5,ms=6
                )
        
        ax.plot(emiss_luc.iloc[0].index,
                emiss_luc.iloc[0].values/1000,
                '--', color='darkgreen',alpha=1, lw=2, label='UnCond LB luc',mec='purple',mew=0.5,ms=3
                )
        
        ax.plot(emiss_luc.iloc[1].index,
                emiss_luc.iloc[1].values/1000,
                '--', color='darkgreen',alpha=1, lw=2, label='Cond LB luc',mec='purple',mew=0.5,ms=3
                )
        


    if np.isnan(np.asarray(NDC.loc[selected_country,['Target_CO2eq_emissions_LB_conditional_LULUCF','Target_CO2eq_emissions_UB_conditional_LULUCF']].values,dtype=float)).any():
        plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                    NDC.loc[selected_country,['Supp_Target_CO2eq_emissions_LB_conditional_LULUCF','Supp_Target_CO2eq_emissions_UB_conditional_LULUCF']].values,
                    label='NDC Condititonal',color='limegreen',marker='o',s=30,zorder=20)
    else:
        plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                    NDC.loc[selected_country,['Target_CO2eq_emissions_LB_conditional_LULUCF','Target_CO2eq_emissions_UB_conditional_LULUCF']].values,
                    label='NDC Condititonal',color='limegreen',marker='o',s=30,zorder=20)


    if np.isnan(np.asarray(NDC.loc[selected_country,['Target_CO2eq_emissions_LB_unconditional_LULUCF','Target_CO2eq_emissions_UB_unconditional_LULUCF']].values,dtype=float)).any():
        plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                    NDC.loc[selected_country,['Supp_Target_CO2eq_emissions_LB_unconditional_LULUCF','Supp_Target_CO2eq_emissions_UB_unconditional_LULUCF']].values,
                    label='NDC Condititonal',color='darkgreen',marker='o',s=30,zorder=20)
    else:
        plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                    NDC.loc[selected_country,['Target_CO2eq_emissions_LB_unconditional_LULUCF','Target_CO2eq_emissions_UB_unconditional_LULUCF']].values,
                    label='NDC Condititonal',color='darkgreen',marker='o',s=30,zorder=20)

    #NDC points
    plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
             co2eq_excl.loc[selected_country,co2eq_excl.columns[5:7]].values,
             label='NDC Condititonal',color='lightblue',marker='x',s=30,zorder=20)


    plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                 co2eq_excl.loc[selected_country,co2eq_excl.columns[3:5]].values,
                 label='NDC Uncondititonal',color='royalblue',marker='x',s=30,zorder=20)
    
    if selected_country in co2eq_nz[co2eq_nz['Neutrality']=='Yes'].index:
        plt.scatter(co2eq_nz.loc[selected_country,'Year'],
                    0,
                    label='Net-zero',color='red',marker='x',s=50,zorder=20)
    
    
    axis_label = "GHG emissions (Mt CO2eq / yr) "

   
if selected_gas=='CO2':
    
    ax.plot(ehist.index,
            ehist.values/1000,
            '-', color='black',alpha=1, lw=2, label='CO2 historical',mec='k',mew=0.5,ms=6
            )

    ax.plot(emiss_co2_excl.iloc[2].index,
            emiss_co2_excl.iloc[2].values/1000,
            'o-', color='violet',alpha=1, lw=2, label='Cond LB',mec='purple',mew=0.5,ms=3
            )

    ax.plot(emiss_co2_excl.iloc[3].index,
            emiss_co2_excl.iloc[3].values/1000,
            'o-', color='violet',alpha=1, lw=2, label='Cond UB',mec='purple',mew=0.5,ms=3
            )

    ax.plot(emiss_co2_excl.iloc[0].index,
            emiss_co2_excl.iloc[0].values/1000,
            'o-', color='grey',alpha=1, lw=2, label='Uncond LB',mec='k',mew=0.5,ms=3
            )

    ax.plot(emiss_co2_excl.iloc[1].index,
            emiss_co2_excl.iloc[1].values/1000,
            'o-', color='grey',alpha=1, lw=2, label='Uncond UB',mec='k',mew=0.5,ms=3
            )

    ax.plot(emiss_paper_co2_uncond.index,
            emiss_paper_co2_uncond.values/1000,
            ':', color='lightgrey',alpha=1, lw=2, label='Uncond',mec='k',mew=0.5,ms=3
            )
    
    ax.plot(emiss_paper_co2_cond.index,
            emiss_paper_co2_cond.values/1000,
            ':', color='pink',alpha=1, lw=2, label='Cond',mec='k',mew=0.5,ms=3
            )
    

    #plot luc emissions:
    if selected_country not in ['Int. Aviation','Int. Shipping']:
        ax.plot(hist_luc_net.loc[selected_country].index,
                hist_luc_net.loc[selected_country].values/1000,
                '-', color='yellowgreen',alpha=1, lw=2, label='CO2eq historical luc net',mec='k',mew=0.5,ms=6
                )
        
        ax.plot(emiss_luc.iloc[0].index,
                emiss_luc.iloc[0].values/1000,
                '--', color='darkgreen',alpha=1, lw=2, label='UnCond LB luc',mec='purple',mew=0.5,ms=3
                )
        
        ax.plot(emiss_luc.iloc[1].index,
                emiss_luc.iloc[1].values/1000,
                '--', color='darkgreen',alpha=1, lw=2, label='Cond LB luc',mec='purple',mew=0.5,ms=3
                )
        


    if np.isnan(np.asarray(NDC.loc[selected_country,['Target_CO2eq_emissions_LB_conditional_LULUCF','Target_CO2eq_emissions_UB_conditional_LULUCF']].values,dtype=float)).any():
        plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                    NDC.loc[selected_country,['Supp_Target_CO2eq_emissions_LB_conditional_LULUCF','Supp_Target_CO2eq_emissions_UB_conditional_LULUCF']].values,
                    label='NDC Condititonal',color='limegreen',marker='o',s=30,zorder=20)
    else:
        plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                    NDC.loc[selected_country,['Target_CO2eq_emissions_LB_conditional_LULUCF','Target_CO2eq_emissions_UB_conditional_LULUCF']].values,
                    label='NDC Condititonal',color='limegreen',marker='o',s=30,zorder=20)


    if np.isnan(np.asarray(NDC.loc[selected_country,['Target_CO2eq_emissions_LB_unconditional_LULUCF','Target_CO2eq_emissions_UB_unconditional_LULUCF']].values,dtype=float)).any():
        plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                    NDC.loc[selected_country,['Supp_Target_CO2eq_emissions_LB_unconditional_LULUCF','Supp_Target_CO2eq_emissions_UB_unconditional_LULUCF']].values,
                    label='NDC Condititonal',color='darkgreen',marker='o',s=30,zorder=20)
    else:
        plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                    NDC.loc[selected_country,['Target_CO2eq_emissions_LB_unconditional_LULUCF','Target_CO2eq_emissions_UB_unconditional_LULUCF']].values,
                    label='NDC Condititonal',color='darkgreen',marker='o',s=30,zorder=20)
    


 
    
    axis_label = "CO2 emissions (Mt / yr) "

if selected_gas == "CH4":
    ax.plot(hist_ch4.loc[selected_country].index,
            hist_ch4.loc[selected_country].values/1000,
            '-', color='black',alpha=1, lw=2, label='CO2eq historical',mec='k',mew=0.5,ms=6
            )

    ax.plot(emiss_ch4.iloc[2].index,
            emiss_ch4.iloc[2].values/1000,
            'o-', color='violet',alpha=1, lw=2, label='Cond LB',mec='purple',mew=0.5,ms=3
            )

    ax.plot(emiss_ch4.iloc[3].index,
            emiss_ch4.iloc[3].values/1000,
            'o-', color='violet',alpha=1, lw=2, label='Cond UB',mec='purple',mew=0.5,ms=3
            )


    ax.plot(emiss_ch4.iloc[0].index,
            emiss_ch4.iloc[0].values/1000,
            'o-', color='grey',alpha=1, lw=2, label='UnCond LB',mec='purple',mew=0.5,ms=3
            )

    ax.plot(emiss_ch4.iloc[1].index,
            emiss_ch4.iloc[1].values/1000,
            'o-', color='grey',alpha=1, lw=2, label='UnCond UB',mec='purple',mew=0.5,ms=3
            )
    
    axis_label = "CH4 emissions (Mt / yr) "

if selected_gas == "N2O":
    ax.plot(hist_n2o.loc[selected_country].index,
            hist_n2o.loc[selected_country].values/1000,
            '-', color='black',alpha=1, lw=2, label='CO2eq historical',mec='k',mew=0.5,ms=6
            )

    ax.plot(emiss_n2o.iloc[2].index,
            emiss_n2o.iloc[2].values/1000,
            'o-', color='violet',alpha=1, lw=2, label='Cond LB',mec='purple',mew=0.5,ms=3
            )

    ax.plot(emiss_n2o.iloc[3].index,
            emiss_n2o.iloc[3].values/1000,
            'o-', color='violet',alpha=1, lw=2, label='Cond UB',mec='purple',mew=0.5,ms=3
            )


    ax.plot(emiss_n2o.iloc[0].index,
            emiss_n2o.iloc[0].values/1000,
            'o-', color='grey',alpha=1, lw=2, label='UnCond LB',mec='purple',mew=0.5,ms=3
            )

    ax.plot(emiss_n2o.iloc[1].index,
            emiss_n2o.iloc[1].values/1000,
            'o-', color='grey',alpha=1, lw=2, label='UnCond UB',mec='purple',mew=0.5,ms=3
            )
    
    axis_label = "N2O emissions (Mt / yr) "




#plotting for adjusted targets

#for net-zero year

# i= 1 if dnzyr>0 else 0

# x = emiss_coun.iloc[i].index
# y1 = emiss_coun.iloc[i].values/1000
# y2 = emiss_nzyr.iloc[i].values/1000
# ax.fill_between(x,y1,y2, where=y2!=y1, facecolor='dodgerblue',interpolate=True,alpha=0.5)

# #for ndc unconditional
# i=1 if duncond>1 else 0
# x = emiss_coun.iloc[i].index
# y1 = emiss_coun.iloc[i].values/1000
# y2 = emiss_uncond.iloc[i].values/1000
# ax.fill_between(x,y1,y2, where=y2!=y1, facecolor='orange',interpolate=True,alpha=0.5)


# #for ndc conditional
# i=3 if dcond>1 else 2
# x = emiss_coun.iloc[i].index
# y1 = emiss_coun.iloc[i].values/1000
# y2 = emiss_cond.iloc[i].values/1000
# ax.fill_between(x,y1,y2, where=y2!=y1, facecolor='brown',interpolate=True,alpha=0.5)

# #for ndc year
# i= 1 if dndcyr>0 else 0

# x = emiss_coun.iloc[i].index
# y1 = emiss_coun.iloc[i].values/1000
# y2 = emiss_ndcyr.iloc[i].values/1000
# ax.fill_between(x,y1,y2, where=y2!=y1, facecolor='khaki',interpolate=True,alpha=0.5)


#add line at 2050:
#ax.axvline(x=2050, color='r', linestyle='--', linewidth=0.5, label='2050')



ax.spines.left.set_position(('data', start))
ax.spines.bottom.set_position(('data', 0))
ax.spines[['top', 'right','left']].set_visible(False)

ax.set_xlim(start,end)
#ax.set_ylim(-5,55)
#ax.set_yticks([0,10,20,30,40,50])
ax.tick_params(axis='y', length=0)
ax.tick_params(labelsize=9)
ax.set_ylabel(axis_label,fontfamily="Arial",fontsize=9,y=0.5)

for tick in ax.get_xticklabels():
    tick.set_fontname("Arial")
    tick.set_fontweight('bold')
for tick in ax.get_yticklabels():
    tick.set_fontname("Arial")
    #tick.set_fontweight('bold')

ax.grid(which='major', axis='y', lw=0.4)


fig2, ax = plt.subplots()


ax.set_title('World',fontfamily="Arial",fontsize=10)

if selected_gas=='CO2':
    
    #ax.plot(emiss_revised_glob_tot_co2_cond.index.values,
    #        emiss_revised_glob_tot_co2_cond.values/1000000,
    #        '-', color='violet',alpha=1, lw=2, label='CO2_excl_cond',mec='k',mew=0.5,ms=6
    #        )
    
    #ax.plot(emiss_revised_glob_tot_co2_uncond.index.values,
    #        emiss_revised_glob_tot_co2_uncond.values/1000000,
    #        '-', color='grey',alpha=1, lw=2, label='CO2_excl_uncond',mec='k',mew=0.5,ms=6
    #        )
    
    
    if pnt2==1:
        ax.plot(pnt2_co2['Cond_LB'].index.values,
                pnt2_co2['Cond_LB'].values,
                '-', color='violet',alpha=1, lw=2, label='CO2_excl_cond',mec='k',mew=0.5,ms=6
                )
    
        ax.plot(pnt2_co2['Uncond_LB'].index.values,
                pnt2_co2['Uncond_LB'].values,
                '-', color='grey',alpha=1, lw=2, label='CO2_excl_uncond',mec='k',mew=0.5,ms=6
                )
        
    if pnt5==1:
        ax.plot(pnt5_co2['Cond_LB'].index.values,
                pnt5_co2['Cond_LB'].values,
                '-', color='violet',alpha=1, lw=2, label='CO2_excl_cond',mec='k',mew=0.5,ms=6
                )
    
        ax.plot(pnt5_co2['Uncond_LB'].index.values,
                pnt5_co2['Uncond_LB'].values,
                '-', color='grey',alpha=1, lw=2, label='CO2_excl_uncond',mec='k',mew=0.5,ms=6
                )
        
    if c1==1:
        ax.plot(c1_co2['Cond_LB'].index.values,
                c1_co2['Cond_LB'].values,
                '-', color='violet',alpha=1, lw=2, label='CO2_excl_cond',mec='k',mew=0.5,ms=6
                )
    
        ax.plot(c1_co2['Uncond_LB'].index.values,
                c1_co2['Uncond_LB'].values,
                '-', color='grey',alpha=1, lw=2, label='CO2_excl_uncond',mec='k',mew=0.5,ms=6
                )
        
    #if c2==1:
    #    ax.plot(c2_co2['Cond_LB'].index.values,
    #            c2_co2['Cond_LB'].values,
    #            '-', color='violet',alpha=1, lw=2, label='CO2_excl_cond',mec='k',mew=0.5,ms=6
    #            )
    
    #    ax.plot(c2_co2['Uncond_LB'].index.values,
    #            c2_co2['Uncond_LB'].values,
    #            '-', color='grey',alpha=1, lw=2, label='CO2_excl_uncond',mec='k',mew=0.5,ms=6
    #            )
    
    if c3==1:
        ax.plot(c3_co2['Cond_LB'].index.values,
                c3_co2['Cond_LB'].values,
                '-', color='violet',alpha=1, lw=2, label='CO2_excl_cond',mec='k',mew=0.5,ms=6
                )
    
        ax.plot(c3_co2['Uncond_LB'].index.values,
                c3_co2['Uncond_LB'].values,
                '-', color='grey',alpha=1, lw=2, label='CO2_excl_uncond',mec='k',mew=0.5,ms=6
                )


   
    ax.plot(emiss_paper_glob_tot_co2_cond.index.values,
            emiss_paper_glob_tot_co2_cond.values/1000000,
            ':', color='pink',alpha=1, lw=2, label='CO2_excl',mec='k',mew=0.5,ms=6
            )  


    ax.plot(emiss_paper_glob_tot_co2_uncond.index.values,
            emiss_paper_glob_tot_co2_uncond.values/1000000,
            ':', color='lightgrey',alpha=1, lw=2, label='CO2_excl',mec='k',mew=0.5,ms=6
            )

if selected_gas=='CO2eq':

    ax.plot(emiss_revised_glob_tot_co2eq_cond.index.values,
            emiss_revised_glob_tot_co2eq_cond.values/1000000,
            '-', color='violet',alpha=1, lw=2, label='CO2_excl_cond',mec='k',mew=0.5,ms=6
            )
    
    ax.plot(emiss_revised_glob_tot_co2eq_uncond.index.values,
            emiss_revised_glob_tot_co2eq_uncond.values/1000000,
            '-', color='grey',alpha=1, lw=2, label='CO2_excl_uncond',mec='k',mew=0.5,ms=6
            )
    
    ax.plot(emiss_paper_glob_tot_co2eq_cond.index.values,
            emiss_paper_glob_tot_co2eq_cond.values/1000000,
            ':', color='pink',alpha=1, lw=2, label='CO2_excl',mec='k',mew=0.5,ms=6
            )  


    ax.plot(emiss_paper_glob_tot_co2eq_uncond.index.values,
            emiss_paper_glob_tot_co2eq_uncond.values/1000000,
            ':', color='lightgrey',alpha=1, lw=2, label='CO2_excl',mec='k',mew=0.5,ms=6
            )

    

ax.spines.left.set_position(('data', start))
ax.spines.bottom.set_position(('data', 0))
ax.spines[['top', 'right','left']].set_visible(False)

ax.set_xlim(start,end)
#ax.set_ylim(-5,55)
#ax.set_yticks([0,10,20,30,40,50])
ax.tick_params(axis='y', length=0)
ax.tick_params(labelsize=9)
ax.set_ylabel("CO2 emissions (Gt/yr) ",fontfamily="Arial",fontsize=9,y=0.5)

for tick in ax.get_xticklabels():
    tick.set_fontname("Arial")
    tick.set_fontweight('bold')
for tick in ax.get_yticklabels():
    tick.set_fontname("Arial")
    #tick.set_fontweight('bold')

ax.grid(which='major', axis='y', lw=0.4)




if glob_tot==0:

    sentence = (
        "<b style='color: black;'>The plot shows non-luc and luc emissions seperately</b> <br>"        
    )

    # Display the sentence
    st.markdown(sentence, unsafe_allow_html=True)



    st.pyplot(fig)

    sentence = (
        "<b style='color: black;'>Legend</b> <br>"
        "Lines <br>"
        
        "<b style='color: black;'>Historical emissions excl. land-use</b> | "
        "<b style='color: grey;'>Unconditional emissions excl. land-use</b> | "
        "<b style='color: violet;'>Conditional emissions excl. land-use</b> | <br>"

        "<b style='color: yellowgreen;'>Historical net land-use managed lands</b> | "
        "<b style='color: darkgreen;'>net land-use managed lands for future</b> | <br> "        
        
        "<b style='color: pink;'>Emissions from our paper version, just for comparison here</b> | <br>"


    )

    # Display the sentence
    st.markdown(sentence, unsafe_allow_html=True)

    sentence = (
            "Dots <br>"
            
            "<b style='color: royalblue;'>Unconditional NDC CO2eq</b> | "
            "<b style='color: lightblue;'>Conditional NDC CO2eq</b> | <br>"
            
            "<b style='color: darkgreen;'>NDC uncond. land-use </b> | "
            "<b style='color: limegreen;'>NDC cond. land-use </b> <br>"
            
            "*Double dots with same colour denote the upper and lower bounds (if exists). <br>"
            )
            
     
    st.markdown(sentence, unsafe_allow_html=True)

else:
    st.pyplot(fig2)

    sentence = (
        "<b style='color: black;'>Legend</b> <br>"
        
        
        "<b style='color: grey;'>Solids lines from revised model</b> | <br>"
        "<b style='color: pink;'>Dotted lines from our paper version, just for comparison here</b> | <br>"


    )

    # Display the sentence
    st.markdown(sentence, unsafe_allow_html=True)






#st.write("Solid line represents the historical emissions")
#st.write("Dots represent emissions as per the NDC target: Unconditional (dark-blue) and Conditional (light-blue)") 





