import altair as alt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import streamlit as st


from model import mod_read_input, mod_nearterm_CO2eq, mod_longterm_CO2eq, mod_emissions_projection

def format_text(value):
    value = int(value)

    if value > 0:
        color = 'red'
    else:
        color = 'green'
    return f"<div style='color:{color}; font-size:20px; text-align: center;'><b>{value} GtCO2eq</b></div>"



st.title("NDC pledges for selected countries")


#read and process NDC data:
@st.cache_data
def get_ndc():
    NDC = mod_read_input.read_ndc()
    
    #process NDC
    co2eq = mod_nearterm_CO2eq.grp_emiss(NDC,'CO2eq')
    co2eq = mod_nearterm_CO2eq.grp_percent_abs(NDC,'CO2eq',data=co2eq)
    co2eq_excl,co2eq_luc = mod_nearterm_CO2eq.to_total_excl(NDC,'CO2eq',data=co2eq)
    co2eq_nz = mod_longterm_CO2eq.grp_nz(NDC,process='co2eq')

    return NDC,co2eq,co2eq_excl,co2eq_luc,co2eq_nz

NDC,co2eq,co2eq_excl,co2eq_luc,co2eq_nz = get_ndc()




#Ask for choices:


#col1,col2=st.columns([2,1])
#col1,col2,col3,col4=st.columns(4)

with st.sidebar:
    
#with col1:
    #selected_country= st.selectbox("Choose Country:",NDC.index)
    selected_country= st.selectbox("Country:",sorted(co2eq_excl.index[co2eq_excl['Processed']=='Yes']))
    

#with col2:
    selected_inventory= st.selectbox("Historical Inventory:",['PRIMAPv5','EDGARv6'])
    hist_co2eq_excl = mod_read_input.read_hist(selected_inventory,'CO2eq','excl') #read historical emissions data

#with col3:
    selected_luc = st.selectbox("Land-use data:",['OSCAR+DGVM','NGHGI'])
    if selected_luc=='OSCAR+DGVM':
        hist_luc_emiss = mod_read_input.read_luc('emiss','OSCAR')
        hist_luc_sink = mod_read_input.read_luc('sink','Grassi')
        hist_luc_net = hist_luc_sink+hist_luc_emiss
    
    if selected_luc=='NGHGI':
        hist_luc_net = mod_read_input.read_luc('net','NGHGI')

#with col4:
    start, end = st.slider("Range of years", 
                           min_value=1850,
                           max_value=2100,
                           value=(2000, 2100),        
                           step=1
                          )
    
    #match = pd.DataFrame(np.arange(273),index=np.arange(1750,2023),columns=['values'])


#st.markdown("<hr>", unsafe_allow_html=True)

col1,col2=st.columns(2)

with col1: 
    st.markdown(f"<div style='text-align: center;'>Adjust emissions level rel. to declared in pledge.<br>(<b>>1</b> = more emissions) </div>",
                unsafe_allow_html=True)
    
with col2:
    st.markdown(f"<div style='text-align: center;'>Adjust year rel. to declared in pledge.<br> (<b>>0</b> = delay it further) </div>",
                unsafe_allow_html=True)
    



col1,col2,col3,col4=st.columns(4)

default=[1.0,1.0,0,0]

with col1:
    duncond= st.slider(label="Unconditional emissions",
                       min_value=0.7,
                       max_value=1.3,
                       value=default[0],
                       step=0.05,
                       #key='slider1'
                       )

with col2:
    dcond= st.slider(label="Conditional emissions",
                     min_value=0.7,
                     max_value=1.3,
                     value=default[1],
                     step=0.05,
                     #key='slider2'
                    )

with col3:
    dndcyr= st.slider(label="NDC target year",
                      min_value=0,
                      max_value=7,
                      value=default[2],
                      step=1,
                      #key='slider3'
                      )

with col4:
    dnzyr= st.slider(label="Net-zero target year",
                     min_value=-5,
                     max_value=7,
                     value=default[3],
                     step=1,
                     #key='slider4'
                     )


#compute the trajectory for selected country:
ehist = hist_co2eq_excl.loc[selected_country]
endc = co2eq_excl.loc[selected_country]
enz = co2eq_nz.loc[selected_country]

#ndc base trajectory
emiss_coun = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz)

#adjusted enhanced/delayed trajectories
emiss_uncond= mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,duncond=duncond)
emiss_cond = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,dcond=dcond)
emiss_ndcyr = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,dndcyr=dndcyr)
emiss_nzyr = mod_emissions_projection.create_timeseries(selected_country,ehist,endc,enz,dnzyr=dnzyr)

#emiss_coun = emiss_nzyr.copy()



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


ax.plot(emiss_coun.iloc[0].index,
        emiss_coun.iloc[0].values/1000,
        ':', color='grey',alpha=1, lw=2, label='CO2eq historical',mec='k',mew=0.5,ms=6
        )

ax.plot(emiss_coun.iloc[1].index,
        emiss_coun.iloc[1].values/1000,
        ':', color='grey',alpha=1, lw=2, label='CO2eq historical',mec='k',mew=0.5,ms=6
        )


plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
            co2eq_excl.loc[selected_country,co2eq_excl.columns[4:6]].values,
            label='NDC Condititonal',color='lightblue',marker='o',s=30,zorder=20)


plt.scatter([co2eq_excl.loc[selected_country,'Year']]*2,
            co2eq_excl.loc[selected_country,co2eq_excl.columns[2:4]].values,
            label='NDC Uncondititonal',color='royalblue',marker='o',s=30,zorder=20)

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

sentence = (
    "<b style='color: black;'>Historical emissions excl. land-use</b> | "
    "<b style='color: royalblue;'>Unconditional NDC</b> | "
    "<b style='color: lightblue;'>Conditional NDC</b> | <br>"
    "<b style='color: yellowgreen;'>Net land-use managed lands</b> | "
    "<b style='color: darkgreen;'>NDC uncond. land-use </b> | "
    "<b style='color: limegreen;'>NDC cond. land-use </b>"

    
)

# Display the sentence
st.markdown(sentence, unsafe_allow_html=True)

sentence = ("*Double dots with same colour denote the upper and lower bounds. <br>"
            "**Shaded area represents the additional emissions added or removed because of the adjustment")
st.markdown(sentence, unsafe_allow_html=True)


#st.write("Solid line represents the historical emissions")
#st.write("Dots represent emissions as per the NDC target: Unconditional (dark-blue) and Conditional (light-blue)") 





