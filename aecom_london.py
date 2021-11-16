import pandas as pd
import streamlit as st
df = pd.read_csv('london.csv')
st.dataframe(df)
