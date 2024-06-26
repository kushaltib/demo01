import altair as alt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap
import streamlit as st


st.title("NDC pledges for selected countries")

#col1,col2=st.columns([2,1])

label = "<label style='display: inline;'>Choose Country:</label>"
st.markdown(label, unsafe_allow_html=True)
country_options=("India","EU27","China")
selected_country= st.selectbox("",options=country_options)

if selected_country=="India":
    st.markdown(textwrap.dedent("""\
                                India
                                """))
else:
    print("No")


