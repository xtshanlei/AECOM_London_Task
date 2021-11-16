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
####################Data preprocessing#######################
st.title('London Fire Station Project - AECOM')
clean_df = pd.read_csv('london.csv')
clean_df['DateAndTimeMobilised'] = pd.to_datetime(clean_df['DateAndTimeMobilised'],dayfirst=True)
clean_df['DateAndTimeArrived'] = pd.to_datetime(clean_df['DateAndTimeArrived'],dayfirst=True)
clean_df['date']= clean_df['DateAndTimeMobilised'].dt.date
clean_df['wait_time'] = clean_df['DateAndTimeArrived']-clean_df['DateAndTimeMobilised']
clean_df['wait_time']=clean_df['wait_time'].dt.total_seconds()
station_df = clean_df.groupby(['DeployedFromStation_Name','date']).nunique().reset_index()[['DeployedFromStation_Name','date','IncidentNumber','Resource_Code']]
station_df['wait_time']=clean_df.groupby(['DeployedFromStation_Name','date']).mean().reset_index()['wait_time']
####################Relationship between number of incidents, number of fire engines and average wait time#######################
st.header('Relationship between number of fire engines, number of fire incidents and average wait time')
st.write('This section shows the 3-dimension relationship between the number of fire engines,the number of fire incidents and average wait time. Our goal here is to control the average waiting time.')
st.markdown('The average wait time of all stations is **{} seconds**, the minimun wait time is **{} seconds**, and the maximum wait time is **{} seconds**. '.format(int(station_df['wait_time'].mean()),int(station_df['wait_time'].min()),int(station_df['wait_time'].max())))
station_df['wait_time']=clean_df.groupby(['DeployedFromStation_Name','date']).mean().reset_index()['wait_time']
relationship_fig = px.scatter_3d(station_df, x="IncidentNumber", y="Resource_Code", z="wait_time",labels={'IncidentNumber':'Number of Incidents','Resource_Code':'Number of Engines','wait_time':'Average Wait Time'},color='DeployedFromStation_Name')
st.plotly_chart(relationship_fig)
####################Highest risk of fire#######################
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


# Display the map chart using Plotly
fig = px.density_mapbox(avg_annual_incidents_per_station, lat='lat', lon='lon', z='IncidentNumber', radius=40,
                        center=dict(lat=convert_add('London')[0], lon=convert_add('London')[1]), zoom=8,
                        mapbox_style="stamen-toner",hover_name='DeployedFromStation_Name',
                        labels = {'IncidentNumber':'No.of Incidents'},range_color=[0,5000])
st.plotly_chart(fig)
# Display the bar chart of the stations with the highest average annual fire incident
top_fig = px.bar(avg_annual_incidents_per_station.sort_values(by='IncidentNumber',ascending=False)[:5],
                x="IncidentNumber",
                y="DeployedFromStation_Name",
                orientation='h',
                labels={'IncidentNumber':'Number of Incidents','DeployedFromStation_Name':'Fire Station'})
top_fig.update_layout(yaxis=dict(autorange="reversed"))
st.plotly_chart(top_fig)
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
