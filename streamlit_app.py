import altair as alt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import streamlit as st


from model import mod_read_input, mod_nearterm_CO2eq, mod_longterm_CO2eq, mod_emissions_projection


st.title("NDC pledges for selected countries")


#read data:
NDC = mod_read_input.read_ndc()


#process NDC
co2eq = mod_nearterm_CO2eq.grp_emiss(NDC,'CO2eq')
co2eq = mod_nearterm_CO2eq.grp_percent_abs(NDC,'CO2eq',data=co2eq)
co2eq_excl = mod_nearterm_CO2eq.to_total_excl(NDC,'CO2eq',data=co2eq)
co2eq_nz = mod_longterm_CO2eq.grp_nz(NDC,process='co2eq')


#Ask for choices:

#country
#col1,col2=st.columns([2,1])
col1,col2,col3=st.columns(3)

#with col1:
#    st.write("Choose Country:")
#with col2:
#    selected_country= st.selectbox("",NDC.index)


with col1:
    #selected_country= st.selectbox("Choose Country:",NDC.index)
    selected_country= st.selectbox("Choose Country:",co2eq_excl.index[co2eq_excl['Processed']=='Yes'])
    

with col2:
    selected_inventory= st.selectbox("Choose Historical Inventory:",['PRIMAPv5','EDGARv6'])
    hist_co2eq_excl = mod_read_input.read_hist(selected_inventory,'CO2eq','excl') #read historical emissions data

with col3:
    start, end = st.slider("Select range of years", 
                           min_value=1850,
                           max_value=2100,
                           value=(2000, 2050),        
                           step=1
                          )
    
    #match = pd.DataFrame(np.arange(273),index=np.arange(1750,2023),columns=['values'])

col1,col2,col3,col4=st.columns(4)



with col1:
    duncond= st.slider(label="Change the unconditional target emissions",
                       min_value=0.7,
                       max_value=1.3,
                       value=1.0,
                       step=0.05
                       )

with col2:
    dcond= st.slider(label="Change the conditional target emissions",
                     min_value=0.7,
                     max_value=1.3,
                     value=1.0,
                     step=0.05
                    )

with col3:
    dndcyr= st.slider(label="Change the NDC target year by ",
                      min_value=0,
                      max_value=7,
                      value=0,
                      step=1
                      )

with col4:
    dnzyr= st.slider(label="Change the net-zero target year by ",
                     min_value=-5,
                     max_value=7,
                     value=0,
                     step=1
                     )    



#compute the trajectory for selected country:
ehist = hist_co2eq_excl.loc[selected_country]
endc = co2eq_excl.loc[selected_country]
enz = co2eq_nz.loc[selected_country]

#ndc based trajectory
emiss_coun = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz)

#adjusted enhanced/delayed trajectories
emiss_uncond = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,duncond=duncond)
emiss_cond = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,dcond=dcond)
emiss_ndcyr = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,dndcyr=dndcyr)
emiss_nzyr = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,dnzyr=dnzyr)

#emiss_coun = emiss_nzyr.copy()

#display the plot
fig, ax = plt.subplots()

ax.set_title(selected_country,fontfamily="Arial",fontsize=10)

ax.plot(hist_co2eq_excl.loc[selected_country].index,
        hist_co2eq_excl.loc[selected_country].values/1000,
        '-', color='black',alpha=1, lw=2, label='CO2eq historical',mec='k',mew=0.5,ms=6
        )


ax.plot(emiss_coun.iloc[0].index,
        emiss_coun.iloc[0].values/1000,
        ':', color='grey',alpha=1, lw=2, label='CO2eq historical',mec='k',mew=0.5,ms=6
        )

ax.plot(emiss_coun.iloc[1].index,
        emiss_coun.iloc[1].values/1000,
        ':', color='grey',alpha=1, lw=2, label='CO2eq historical',mec='k',mew=0.5,ms=6
        )


plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
            co2eq_excl.loc[selected_country,co2eq.columns[4:6]].values,
            label='NDC Condititonal',color='lightblue',marker='o',s=30,zorder=20)


plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
            co2eq_excl.loc[selected_country,co2eq.columns[2:4]].values,
            label='NDC Uncondititonal',color='royalblue',marker='o',s=30,zorder=20)

#plotting for adjusted targets
x = emiss_coun.iloc[1].index
y1 = emiss_coun.iloc[1].values/1000
y2 = emiss_nzyr.iloc[1].values/1000
ax.fill_between(x,y1,y2, where=y2!=y1, facecolor='dodgerblue',interpolate=True,alpha=0.6)



ax.spines.left.set_position(('data', start))
ax.spines.bottom.set_position(('data', 0))
ax.spines[['top', 'right','left']].set_visible(False)

ax.set_xlim(start,end)
#ax.set_ylim(-5,55)
#ax.set_yticks([0,10,20,30,40,50])
ax.tick_params(axis='y', length=0)
ax.tick_params(labelsize=9)
ax.set_ylabel("GHG emissions excl. LULUCF (Mt CO2eq / yr) ",fontfamily="Arial",fontsize=9,y=0.5)

for tick in ax.get_xticklabels():
    tick.set_fontname("Arial")
    tick.set_fontweight('bold')
for tick in ax.get_yticklabels():
    tick.set_fontname("Arial")
    #tick.set_fontweight('bold')

ax.grid(which='major', axis='y', lw=0.4)

st.pyplot(fig)

st.write("Solid line represents the historical emissions")
st.write("Dots represent emissions as per the NDC target: Unconditional (dark-blue) and Conditional (light-blue)") 





