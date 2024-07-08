import streamlit as st
import pandas as pd
import numpy as np

title = "Platform Monitoring"
sidebar_name = "Future Developments"


def run():

    st.title(title)
    st.write(''' 
    
    Limited time and ongoing learnings left several items for future development

    * Full dockerization of all components
    * Backup strategy for customer data in the docker environment
    * Full and integrated monitoring strategy for all system components
      * Data quality
      * Model performance
      * System health 
      * 

    '''
    )