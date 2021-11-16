####################Preparation#######################

import pandas as pd
import streamlit as st

st.title('London Fire Station Project - AECOM')

####################Simulation#######################


class Station(object): # Define the fire station class
  def __init__(self, env, num_engines, station_name):
    self.env = env
    self.name = station_name
    self.engines = simpy.Resource(env, num_engines)

  def mobilisation(self, fire_incident): # Define the
    yield self.env.timeout(generate_attendence_time(self.name)/60)
