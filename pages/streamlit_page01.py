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



def page01(selected_fitmethod,selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg,gmax,dg,asm,corr,emiss_coun,hist_co2eq_excl,emiss_paper,co2eq_excl,NDC,hist_luc_net,start,end):

    #--controlling shifts in NDC levels, NDC year and NZ year
    col1,col2=st.columns(2)

    with col1: 
        st.markdown(f"<div style='text-align: center;'>Adjust emissions w.r.t. declared targets<br>(<b>>1</b> = more emissions) </div>",
                unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<div style='text-align: center;'>Adjust year w.r.t declared targets<br> (<b>>0</b> = delay it further) </div>",
                unsafe_allow_html=True)
    

    col1,col2,col3,col4=st.columns(4)

    default=[1.0,1.0,0,0]

    with col1:
        duncond= st.slider(label="Uncond. emissions",
                       min_value=0.7,
                       max_value=1.3,
                       value=default[0],
                       step=0.05,
                       #key='slider1'
                       )

    with col2:
        dcond= st.slider(label="Cond. emissions",
                     min_value=0.7,
                     max_value=1.3,
                     value=default[1],
                     step=0.05,
                     #key='slider2'
                    )

    with col3:
        dndcyr= st.slider(label="NDC year",
                      min_value=0,
                      max_value=10,
                      value=default[2],
                      step=1,
                      #key='slider3'
                      )

    with col4:
        dnzyr= st.slider(label="Net-zero year",
                     min_value=-10,
                     max_value=10,
                     value=default[3],
                     step=1,
                     #key='slider4'
                     )


    #--collect historical emissions, NDC and NZ information for selected country:
    #ehist = hist_co2eq_excl.loc[selected_country]




    #--------------------------------------------------------------------------------------------
    #--adjusted enhanced/delayed trajectories

    if selected_fitmethod=='Olivier old':
        #----Olivier's method
        emiss_uncond= mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,gmax=gmax/100,dg0=dg/100,corr=corr,asm=asm,duncond=duncond)
        emiss_cond = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,gmax=gmax/100,dg0=dg/100,corr=corr,asm=asm,dcond=dcond)
        emiss_ndcyr = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,gmax=gmax/100,dg0=dg/100,corr=corr,asm=asm,dndcyr=dndcyr)
        emiss_nzyr = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,gmax=gmax/100,dg0=dg/100,corr=corr,asm=asm,dnzyr=dnzyr)
        emiss_allchg = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,eneg=100/eneg,gmax=gmax/100,dg0=dg/100,corr=corr,asm=asm,duncond=duncond,dcond=dcond,dndcyr=dndcyr,dnzyr=dnzyr)

    if selected_fitmethod=='Olivier revised':
        #----New method
        emiss_uncond= mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,duncond=duncond)
        emiss_cond = mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,dcond=dcond)
        emiss_ndcyr = mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,dndcyr=dndcyr)
        emiss_nzyr = mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,dnzyr=dnzyr)
        emiss_allchg = mod_emissions_projection_method03.create_timeseries_equ(selected_country,ehist,endc,enz,ndc_ch4,ndc_n2o,duncond=duncond,dcond=dcond,dndcyr=dndcyr,dnzyr=dnzyr)


    #show the change in cumm. CO2eq with each type of change
    #for net-zero year
    i= 1 if dnzyr>0 else 0
    cumm_nzyr = emiss_nzyr.iloc[i].sum()/1000000 -emiss_coun.iloc[i].sum()/1000000

    #for ndc unconditional
    i=1 if duncond>1 else 0
    cumm_uncond = emiss_uncond.iloc[i].sum()/1000000 - emiss_coun.iloc[i].sum()/1000000

    #for ndc conditional
    i=3 if dcond>1 else 2
    cumm_cond = emiss_cond.iloc[i].sum()/1000000 - emiss_coun.iloc[i].sum()/1000000

    #for ndc year
    i= 1 if dndcyr>0 else 0
    cumm_ndcyr = emiss_ndcyr.iloc[i].sum()/1000000 - emiss_coun.iloc[i].sum()/1000000




    sentence = (
        "Cumulative emissions "
        "<b style='color: green;'>avoided</b> or "
        "<b style='color: red;'>added</b>"
        " for each type of change."
        )

    # Display the sentence
    st.markdown(sentence, unsafe_allow_html=True)


    col1,col2,col3,col4=st.columns(4)

    with col1:
        st.markdown(format_text(cumm_uncond), unsafe_allow_html=True)

    with col2:
        st.markdown(format_text(cumm_cond), unsafe_allow_html=True)

    with col3:
        st.markdown(format_text(cumm_ndcyr), unsafe_allow_html=True)

    with col4:
        st.markdown(format_text(cumm_nzyr), unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    #display the plot
    fig, ax = plt.subplots()

    ax.set_title(selected_country,fontfamily="Arial",fontsize=10)

    ax.plot(hist_co2eq_excl.loc[selected_country].index,
            hist_co2eq_excl.loc[selected_country].values/1000,
            '-', color='black',alpha=1, lw=2, label='CO2eq historical',mec='k',mew=0.5,ms=6
            )

    ax.plot(ehist.index,
            ehist.values/1000,
            '-', color='dodgerblue',alpha=1, lw=2, label='CO2 historical',mec='k',mew=0.5,ms=6
         )

    ax.plot(emiss_coun.iloc[2].index,
            emiss_coun.iloc[2].values/1000,
            'o-', color='violet',alpha=1, lw=2, label='Cond LB',mec='purple',mew=0.5,ms=3
            )

    ax.plot(emiss_coun.iloc[3].index,
            emiss_coun.iloc[3].values/1000,
            'o-', color='violet',alpha=1, lw=2, label='Cond UB',mec='purple',mew=0.5,ms=3
            )



    ax.plot(emiss_coun.iloc[0].index,
            emiss_coun.iloc[0].values/1000,
            'o-', color='grey',alpha=1, lw=2, label='Uncond LB',mec='k',mew=0.5,ms=3
            )

    ax.plot(emiss_coun.iloc[1].index,
            emiss_coun.iloc[1].values/1000,
            'o-', color='grey',alpha=1, lw=2, label='Uncond UB',mec='k',mew=0.5,ms=3
            )

    ax.plot(emiss_paper.index,
            emiss_paper.values/1000,
            ':', color='pink',alpha=1, lw=2, label='Uncond UB',mec='k',mew=0.5,ms=3
            )


    plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                co2eq_excl.loc[selected_country,co2eq_excl.columns[5:7]].values,
                label='NDC Condititonal',color='lightblue',marker='x',s=30,zorder=20)


    plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
                co2eq_excl.loc[selected_country,co2eq_excl.columns[3:5]].values,
                label='NDC Uncondititonal',color='royalblue',marker='x',s=30,zorder=20)

    plt.scatter(co2eq_nz .loc[selected_country,'Year'],
                0,
                label='Net-zero',color='red',marker='x',s=50,zorder=20)




    #plot base year values from NDC
    plt.scatter(NDC.loc[selected_country,'Base_year'],
                NDC.loc[selected_country,'Base_CO2eq_emissions_Total-net'],
                label='Base net CO2eq',color='red',marker='o',edgecolors='orange',linewidths=1.5,s=40,zorder=20)

    plt.scatter(NDC.loc[selected_country,'Base_year'],
                NDC.loc[selected_country,'Base_CO2eq_emissions_Total-excl'],
                label='Base excl CO2eq',color='grey',marker='o',edgecolors='black',linewidths=2,s=40,zorder=20)




    #plotting for adjusted targets

    #for net-zero year
    i= 1 if dnzyr>0 else 0

    x = emiss_coun.iloc[i].index
    y1 = emiss_coun.iloc[i].values/1000
    y2 = emiss_nzyr.iloc[i].values/1000
    ax.fill_between(x,y1,y2, where=y2!=y1, facecolor='dodgerblue',interpolate=True,alpha=0.5)

    #for ndc unconditional
    i=1 if duncond>1 else 0
    x = emiss_coun.iloc[i].index
    y1 = emiss_coun.iloc[i].values/1000
    y2 = emiss_uncond.iloc[i].values/1000
    ax.fill_between(x,y1,y2, where=y2!=y1, facecolor='orange',interpolate=True,alpha=0.5)


    #for ndc conditional
    i=3 if dcond>1 else 2
    x = emiss_coun.iloc[i].index
    y1 = emiss_coun.iloc[i].values/1000
    y2 = emiss_cond.iloc[i].values/1000
    ax.fill_between(x,y1,y2, where=y2!=y1, facecolor='brown',interpolate=True,alpha=0.5)

    #for ndc year
    i= 1 if dndcyr>0 else 0

    x = emiss_coun.iloc[i].index
    y1 = emiss_coun.iloc[i].values/1000
    y2 = emiss_ndcyr.iloc[i].values/1000
    ax.fill_between(x,y1,y2, where=y2!=y1, facecolor='khaki',interpolate=True,alpha=0.5)


    #plot luc emissions:
    if selected_country not in ['Int. Aviation','Int. Shipping']:
        ax.plot(hist_luc_net.loc[selected_country].index,
                hist_luc_net.loc[selected_country].values/1000,
                '-', color='yellowgreen',alpha=1, lw=2, label='CO2eq historical luc net',mec='k',mew=0.5,ms=6
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



    #plot net emissions:
    if selected_country not in ['Int. Aviation','Int. Shipping']:
        data_len = min(len(hist_co2eq_excl.loc[selected_country].values),len(hist_luc_net.loc[selected_country].values))

        ax.plot(hist_luc_net.loc[selected_country].index[-data_len:],
                hist_co2eq_excl.loc[selected_country].values[-data_len:]/1000+hist_luc_net.loc[selected_country].values[-data_len:]/1000,
                '--', color='orange',alpha=1, lw=2, label='CO2eq historical net',mec='k',mew=0.5,ms=6
                ) 



    ax.spines.left.set_position(('data', start))
    ax.spines.bottom.set_position(('data', 0))
    ax.spines[['top', 'right','left']].set_visible(False)

    ax.set_xlim(start,end)
    #ax.set_ylim(-5,55)
    #ax.set_yticks([0,10,20,30,40,50])
    ax.tick_params(axis='y', length=0)
    ax.tick_params(labelsize=9)
    ax.set_ylabel("GHG emissions (Mt CO2eq / yr) ",fontfamily="Arial",fontsize=9,y=0.5)

    for tick in ax.get_xticklabels():
        tick.set_fontname("Arial")
        tick.set_fontweight('bold')
    for tick in ax.get_yticklabels():
        tick.set_fontname("Arial")
        #tick.set_fontweight('bold')

    ax.grid(which='major', axis='y', lw=0.4)

    st.pyplot(fig)

    st.markdown("For India and China - it CO2 emissions and for others CO2eq", unsafe_allow_html=True)

    sentence = (
        "<b style='color: black;'>Historical emissions excl. land-use</b> | "
        "<b style='color: royalblue;'>Unconditional NDC</b> | "
        "<b style='color: lightblue;'>Conditional NDC</b> | <br>"
        "<b style='color: yellowgreen;'>Historical net land-use managed lands</b> | "
        "<b style='color: darkgreen;'>NDC uncond. land-use </b> | "
        "<b style='color: limegreen;'>NDC cond. land-use </b> <br>"
        "<b style='color: orange;'>Historical emissions net</b> | "


        )

    # Display the sentence
    st.markdown(sentence, unsafe_allow_html=True)

    sentence = ("*Double dots with same colour denote the upper and lower bounds. <br>"
                "**Shaded area represents the additional emissions added or removed because of the adjustment")
    st.markdown(sentence, unsafe_allow_html=True)


    #st.write("Solid line represents the historical emissions")
    #st.write("Dots represent emissions as per the NDC target: Unconditional (dark-blue) and Conditional (light-blue)") 





