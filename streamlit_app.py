import altair as alt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import streamlit as st


from model import mod_read_input, mod_nearterm_CO2eq, mod_longterm_CO2eq


st.title("NDC pledges for selected countries")


#read data:
NDC = mod_read_input.read_ndc()


#process NDC
co2eq = mod_nearterm_CO2eq.grp_emiss(NDC,'CO2eq')
co2eq = mod_nearterm_CO2eq.grp_percent_abs(NDC,'CO2eq',data=co2eq)
co2eq_excl = mod_nearterm_CO2eq.to_total_excl(NDC,'CO2eq',data=co2eq)

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
    selected_inventory= st.selectbox("Choose Historical Inventory:",['PRIMAPv5'])
    hist_co2eq_excl = mod_read_input.read_hist(selected_inventory,'CO2eq','excl') #read historical emissions data

with col3:
    start, end = st.slider("Select range of years", 
                           min_value=1850,
                           max_value=2100,
                           value=(2000, 2050),        
                           step=1
                          )
    
    #match = pd.DataFrame(np.arange(273),index=np.arange(1750,2023),columns=['values'])


#display the plot
fig, ax = plt.subplots()

ax.plot(hist_co2eq_excl.loc[selected_country].index,
        hist_co2eq_excl.loc[selected_country].values/1000,
        '-', color='black',alpha=1, lw=2, label='CO2eq historical',mec='k',mew=0.5,ms=6
        )


plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
            co2eq_excl.loc[selected_country,co2eq.columns[4:6]].values,
            label='NDC Condititonal',color='lightblue',marker='o',s=30,zorder=20)


plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
            co2eq_excl.loc[selected_country,co2eq.columns[2:4]].values,
            label='NDC Uncondititonal',color='royalblue',marker='o',s=30,zorder=20)



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

st.write("Line represents the historical emissions")
st.write("Dots represent emissions as per the NDC target: Unconditional (dark-blue) and Conditional (light-blue)") 





