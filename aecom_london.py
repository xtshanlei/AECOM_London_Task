####################Preparation#######################

import pandas as pd
import streamlit as st
from geopy.geocoders import GoogleV3
import random
import simpy
locator = GoogleV3(api_key=st.secrets['google_api'])
@st.cache
def convert_add(add):
  location = locator.geocode(add)
  return location.latitude, location.longitude

st.title('London Fire Station Project - AECOM')
clean_df = pd.read_csv('london.csv')


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
random.seed(42)
station = st.selectbox('Please select the fire station you want to simulate',(clean_df['DeployedFromStation_Name'].unique()))
num_engines= st.slider('Please choose the number of fire engines',1,50,1)
# Run the simulation
env = simpy.Environment()
env.process(run_station(env, 2,'Acton'))
env.run(until=100)
st.write(wait_times)
