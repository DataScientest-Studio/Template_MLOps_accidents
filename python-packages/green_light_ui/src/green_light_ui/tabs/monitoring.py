import streamlit as st
import pandas as pd
import numpy as np

title = "Platform Monitoring"
sidebar_name = "Future Developments"


def run():

    st.title(title)
    st.write(
        """ 
    
    Limited time left several items for future development

    * Full dockerization of all components (MLFLOW)
    * Add logs to our Python packages
    * Backup strategy for customer data in the docker environment
    * Full and integrated monitoring strategy for all system components
      * Data quality 
      * Model performance
      * System health 
      * Security situation
    * Systematic monitoring of data drift and model rot
      * Define criteria for data drift & model rot
      * Implement sensors and measurement
      * Implement dashboards and 'actions'
    * System health
      * Availability measurement
      * Alerts 
      * Load supervision and capacity management 
    * Security hardening 
      * Put all Docker exposed ports under authorization 
      * Restrict IP-domains for access
      * Alerts for spurious access attempts
      ...
      


    """
    )
