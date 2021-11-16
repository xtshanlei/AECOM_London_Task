####################Preparation#######################

import pandas as pd
import streamlit as st
from geopy.geocoders import GoogleV3
import random
import simpy
import plotly.express as px
import plotly.graph_objects as go

locator = GoogleV3(api_key=st.secrets['google_api'])
@st.cache
def convert_add(add):
  location = locator.geocode(add)
  return location.latitude, location.longitude

st.title('London Fire Station Project - AECOM')
clean_df = pd.read_csv('london.csv')

####################Visualisation#######################
# Anually
st.header('Annual Average Number of Fire Incidents for Each Station')
st.write('The area with highest risk of fire incident is the centre of London. The busiest station is the Soho Fire Station')
annual_incidents_per_station= clean_df.groupby(['DeployedFromStation_Name','CalYear']).nunique()['IncidentNumber'].reset_index() # Average number of incidents for each station for each year
avg_annual_incidents_per_station = annual_incidents_per_station.groupby(['DeployedFromStation_Name']).mean()['IncidentNumber'].reset_index() # Average number of incidents for each station

# Convert fire station into coordinates using Google API
lat_lst = []
lon_lst = []
for add in avg_annual_incidents_per_station['DeployedFromStation_Name']:
  try: lat,lon = convert_add(add+' fire station, london, uk')
  except: print(add)
  lat_lst.append(lat)
  lon_lst.append(lon)
avg_annual_incidents_per_station['lat']= lat_lst
avg_annual_incidents_per_station['lon']= lon_lst



fig = px.density_mapbox(avg_annual_incidents_per_station, lat='lat', lon='lon', z='IncidentNumber', radius=40,
                        center=dict(lat=convert_add('London')[0], lon=convert_add('London')[1]), zoom=8,
                        mapbox_style="stamen-toner",hover_name='DeployedFromStation_Name',
                        labels = {'IncidentNumber':'No.of Incidents'},range_color=[0,5000])
st.plotly_chart(fig)

top_fig = px.bar(avg_annual_incidents_per_station, x="IncidentNumber", y="DeployedFromStation_Name", orientation='h')

# Hourly
st.header('Hourly Average Number of Fire Incidents for Each Station')
st.write('The figure shows the average fire incidents each hour for each station. The riskiest time of fire incidents during a day is evening between 17:00 and 19:00.  Hit the play button below or slide to choose the hour to explore more.')
hour_incidents_per_station = clean_df.groupby(['DeployedFromStation_Name','date','HourOfCall']).count()
avg_hourly_incidents_per_station = hour_incidents_per_station.groupby(['DeployedFromStation_Name','HourOfCall']).mean()['IncidentNumber'].reset_index()
hour_lat_list = []
hour_lon_list = []
for station in avg_hourly_incidents_per_station['DeployedFromStation_Name']:
  lat = avg_annual_incidents_per_station[avg_annual_incidents_per_station['DeployedFromStation_Name']==station]['lat'].values[0]
  lon = avg_annual_incidents_per_station[avg_annual_incidents_per_station['DeployedFromStation_Name']==station]['lon'].values[0]
  hour_lat_list.append(lat)
  hour_lon_list.append(lon)
avg_hourly_incidents_per_station['lat']=hour_lat_list
avg_hourly_incidents_per_station['lon']=hour_lon_list
hour_fig = px.density_mapbox(avg_hourly_incidents_per_station, lat='lat', lon='lon', z='IncidentNumber', radius=40,
                        center=dict(lat=convert_add('London')[0], lon=convert_add('London')[1]), zoom=8,
                        mapbox_style="stamen-toner",hover_name='DeployedFromStation_Name',
                        labels = {'IncidentNumber':'No.of Incidents'},
                        range_color=[avg_hourly_incidents_per_station['IncidentNumber'].min(),avg_hourly_incidents_per_station['IncidentNumber'].max()],
                        animation_frame='HourOfCall')
st.plotly_chart(hour_fig)
####################Simulation#######################
