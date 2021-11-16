####################Preparation#######################

import pandas as pd
import streamlit as st
from geopy.geocoders import GoogleV3
import random
import simpy
import plotly.express as px
locator = GoogleV3(api_key=st.secrets['google_api'])
@st.cache
def convert_add(add):
  location = locator.geocode(add)
  return location.latitude, location.longitude

st.title('London Fire Station Project - AECOM')
clean_df = pd.read_csv('london.csv')

####################Visualisation#######################
# Anually
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

# Hourly
hour_incidents_per_station = clean_df.groupby(['DeployedFromStation_Name','HourOfCall']).count()
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
hour_fig = px.density_mapbox(avg_hourly_incidents_per_station, lat='lat', lon='lon', z='IncidentNumber', radius=20,
                        center=dict(lat=convert_add('London')[0], lon=convert_add('London')[1]), zoom=7,
                        mapbox_style="stamen-toner",hover_name='DeployedFromStation_Name',
                        labels = {'IncidentNumber':'No.of Incidents'},
                        range_color=[avg_hourly_incidents_per_station['IncidentNumber'].min(),avg_hourly_incidents_per_station['IncidentNumber'].max()],
                        animation_frame='HourOfCall')
st.plotly_chart(hour_fig)
####################Simulation#######################
def generate_attendence_time(station): # Generate random attendence time based on historical data
  mu,sigma = clean_df[clean_df['DeployedFromStation_Name']==station]['AttendanceTimeSeconds'].describe()['mean'],clean_df[clean_df['DeployedFromStation_Name']==station]['AttendanceTimeSeconds'].describe()['std']
  return abs(np.random.normal(mu, sigma, 1))

def generate_incident_time_gap(station): # Generate random fire incident for a certain station
  incident_time_gap = clean_df[clean_df['DeployedFromStation_Name']==station].sort_values(by='DateAndTimeMobilised').reset_index()['DateAndTimeMobilised'].diff().reset_index()
  mu, sigma = incident_time_gap['DateAndTimeMobilised'][1:].dt.total_seconds().div(60).astype(int).describe()['mean'],incident_time_gap['DateAndTimeMobilised'][1:].dt.total_seconds().div(60).astype(int).describe()['std']
  return abs(np.random.normal(mu, sigma, 1))

class Station(object): # Define the fire station class
  def __init__(self, env, num_engines, station_name):
    self.env = env
    self.name = station_name
    self.engines = simpy.Resource(env, num_engines)

  def mobilisation(self, fire_incident): # Simulate the turnout process based on each station's attendence time
    yield self.env.timeout(generate_attendence_time(self.name)/60)

def Dealing_with_Fire(env, fire_incident, station): # Dealing with the fire incident for each station based on the attendence time
  # Fire incidents occurs
  occur_time = env.now
  with station.engines.request() as request:
    yield request
    yield env.process(station.mobilisation(fire_incident))
  # Fire turned out
  wait_times.append(float(env.now - occur_time))


def run_station(env, num_engines, station_name): # Define the station running
  station = Station(env, num_engines, station_name)
  fire_incident=1
  env.process(Dealing_with_Fire(env, fire_incident, station))

  while True:
    yield env.timeout(generate_incident_time_gap(station.name))  # Wait a bit before generating a new fire incident
    fire_incident += 1
    env.process(Dealing_with_Fire(env, fire_incident, station))

def get_average_wait_time(wait_times): # Calculate average wait time
  average_wait = statistics.mean(wait_times)
  # Pretty print the results
  minutes, frac_minutes = divmod(average_wait, 1)
  seconds = frac_minutes * 60
  return round(minutes), round(seconds)


wait_times = []
station = st.selectbox('Please select the fire station you want to simulate',(clean_df['DeployedFromStation_Name'].unique()))
num_engines= st.slider('Please choose the number of fire engines',1,50,1)
# Run the simulation
env = simpy.Environment()
env.process(run_station(env, 2,'Acton'))
env.run(until=100)
st.write(wait_times)
