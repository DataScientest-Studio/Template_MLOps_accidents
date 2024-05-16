# external
import json
import os
from pathlib import Path
import requests
import sys

# internal:
root_path = Path(os.path.realpath(__file__)).parents[2]
sys.path.append(os.path.join(root_path, "src", "data"))
from make_dataset import main, make_dataset_without_saving

# paths:
path_data_raw = os.path.join(root_path, "data", "raw")
path_data_interim = os.path.join(root_path, "data", "interim")
path_data_preprocessed = os.path.join(root_path, "data", "preprocessed")
path_data_id = os.path.join(root_path, "src", "data", "data_id.json")

# Load data_id:
with open(path_data_id, 'r') as file:
    data_id = json.load(file)


# Functions:
def download_file(input_url, output_file):
    """
    Check if output_file exists. \n
    If not, download a file from an url and save it \n
    under the specified path and name.

    Args:
    - input_url: url of the file to download
    - output_file: path and name of the file to save.
    """
    if os.path.isfile(output_file) is False:
        response = requests.get(input_url)
        if response.status_code == 200:
            # Process the response content as needed
            content = response.text
            text_file = open(output_file, "wb")
            text_file.write(content.encode("utf-8"))  # to be check...
            text_file.close()
            print(f"{output_file} loaded")
        else:
            print(f"Error accessing the object {input_url}:",
                  response.status_code)
    else:
        print(f"File {output_file} already exists, no need to download it.")


# Scripts:
def data_update(year_list):
    """
    Download new files from datagouv.fr (if they don't exist).
    Merge and save them into one file by category in data/interim.
    Make preprocessing via main function from make_dataset module
    to save X/y_train/test.csv in data/preprocessed.
    Args:
        - year_list: a list of years between 2019 and 2020.
    """
    output_path = os.path.join(root_path, "data", "raw")

    # download data files according to the year list
    file_list_template = ["caracteristiques", "lieux", "usagers", "vehicules"]

    for year in year_list:
        for item in file_list_template:
            input_url = data_id[str(year)][item]["url"]
            filename = f'{item}-{year}.csv'
            output_data_file = os.path.join(output_path, filename)
            download_file(input_url, output_data_file)

    # Get existing years in data/raw files:
    year_list = []
    for filename in os.listdir(path_data_raw):
        year = filename[-8:-4]
        if year not in year_list:
            year_list.append(year)

    # Merge individual year files into one by category
    # and overwrite in data/interim:
    for file_template in file_list_template:
        output_filename = os.path.join(path_data_interim,
                                       f"{file_template}.csv")
        with open(output_filename, "w") as merged_file:
            for index, year in enumerate(year_list):
                input_filename = os.path.join(path_data_raw,
                                              f"{file_template}-{year}.csv")
                with open(input_filename, "r") as file:
                    # Throw away header on all but first file
                    if index != 0:
                        file.readline()
                    merged_file.write(file.read())

    # Preprocess data using main function from make_dataset.py:
    sys.path.append(os.path.join(root_path, "src", "data"))

    main(input_filepath=path_data_interim,
         output_filepath=path_data_preprocessed)

    print("Data updated and preprocessed successfully.")


def data_update_without_saving(year_list):
    """
    """
    output_path = os.path.join(root_path, "data", "raw")

    # download data files according to the year list
    file_list_template = ["caracteristiques", "lieux", "usagers", "vehicules"]

    for year in year_list:
        for item in file_list_template:
            input_url = data_id[str(year)][item]["url"]
            filename = f'{item}-{year}.csv'
            output_data_file = os.path.join(output_path, filename)
            download_file(input_url, output_data_file)

    # Get existing years in data/raw files:
    year_list = []
    for filename in os.listdir(path_data_raw):
        year = filename[-8:-4]
        if year not in year_list:
            year_list.append(year)

    # DONE CHANGE: Merge individual year files into one by category
    # and overwrite in data/interim:
    for file_template in file_list_template:
        output_filename = os.path.join(path_data_interim,
                                       f"eval_{file_template}.csv")
        with open(output_filename, "w") as merged_file:
            for index, year in enumerate(year_list):
                input_filename = os.path.join(path_data_raw,
                                              f"{file_template}-{year}.csv")
                with open(input_filename, "r") as file:
                    # Throw away header on all but first file
                    if index != 0:
                        file.readline()
                    merged_file.write(file.read())

    # DONE CHANGE: Preprocess data using main function from make_dataset.py:
    sys.path.append(os.path.join(root_path, "src", "data"))

    make_dataset_without_saving(input_filepath=path_data_interim,
                                output_filepath=path_data_preprocessed)

    print("Data updated and preprocessed successfully.")


if __name__ == '__main__':
    data_update(year_list=[2019, 2019])
