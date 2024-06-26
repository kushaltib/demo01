import altair as alt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import streamlit as st


from model import mod_read_input, mod_nearterm_CO2eq, mod_longterm_CO2eq


st.title("NDC pledges for selected countries")


NDC = mod_read_input.read_ndc()
co2eq = mod_nearterm_CO2eq.grp_emiss(NDC,'CO2eq')

col1,col2=st.columns([2,1])

with col1:
    label = "Choose Country:"
    st.header(label)
with col2:
    selected_country= st.selectbox("",NDC.index)


#display the summary



st.write(co2eq.loc[selected_country])

