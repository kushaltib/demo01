import altair as alt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import streamlit as st


st.title("NDC pledges for selected countries")

col1,col2=st.columns([2,1])

with col1:
    label = "Choose Country:"
    st.header(label)
with col2:
    country_options=("India","EU27","China")
    selected_country= st.selectbox("",options=country_options)

if selected_country=="India":
    st.markdown(textwrap.dedent("""\
                                India
                                """))
else:
    st.markdown(textwrap.dedent("""\
                                No-way!
                                """))


