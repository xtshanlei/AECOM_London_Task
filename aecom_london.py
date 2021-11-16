import pandas as pd
import streamlit as st
df = pd.read_csv('LFB Mobilisation data from January 2016.csv')
st.dataframe(df)
