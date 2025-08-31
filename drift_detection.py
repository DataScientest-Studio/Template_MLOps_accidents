import pandas as pd
from evidently.dashboard import Dashboard
from evidently.tabs import DataDriftTab

train_data = pd.read_csv('data/X_train.csv')
test_data = pd.read_csv('data/X_test.csv')

dashboard = Dashboard(tests=[DataDriftTab()])
dashboard.calculate(train_data, test_data)

dashboard.save("drift_report.html")

