import os
from pathlib import Path

root_path = Path(os.path.realpath(__file__)).parents[2]
raw_data_relative_path = os.path.join(root_path, "data", "raw")
preprocessed_data_relative_path = os.path.join(root_path, "data", "preprocessed")
interim_data_relative_path = os.path.join(root_path, "data", "interim")

os.makedirs(raw_data_relative_path)
os.makedirs(preprocessed_data_relative_path)
os.makedirs(interim_data_relative_path)
