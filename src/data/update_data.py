# external
import os
from pathlib import Path
import requests
import sys

# internal:
root_path = Path(os.path.realpath(__file__)).parents[2]
sys.path.append(os.path.join(root_path, "src", "data"))
from make_dataset import main

# paths:
path_data_raw = os.path.join(root_path, "data", "raw")
path_data_interim = os.path.join(root_path, "data", "interim")
path_data_preprocessed = os.path.join(root_path, "data", "preprocessed")


# Functions:
def download_file(input_url, output_file):
    """
    Donwload a file from an url and save it under the specified path and name.
    Args:
    - input_url: url of the file to download
    - output_file: path and name of the file to save.
    """
    response = requests.get(input_url)
    if response.status_code == 200:
        # Process the response content as needed
        content = response.text
        text_file = open(output_file, "wb")
        text_file.write(content.encode("utf-8"))  # to be check...
        text_file.close()
        print(f"{output_file} loaded")
    else:
        print(f"Error accessing the object {input_url}:", response.status_code)


# Script:
def data_update(year_list):
    output_path = os.path.join(root_path, "data", "raw")
    http_url = "https://www.data.gouv.fr/fr/datasets/r/"
    # year_list = [2019, 2020]

    # download list of ressources from gouv.fr
    output_file = os.path.join(output_path, "ressources.csv")
    download_file("https://www.data.gouv.fr/resources.csv", output_file)

    # download data files according to the year list
    file_list_template = ["caracteristiques", "lieux", "usagers", "vehicules"]
    data_files_list = [f'{item}-{year}.csv'
                       for item in file_list_template for year in year_list]

    with open(output_file, "r", encoding="utf-8") as my_file:
        contents = my_file.readline()
        while contents:
            for filename in data_files_list:
                if filename in contents:
                    # 9 = ressource id
                    input_url = http_url + contents.split(";")[9][1:-1]
                    output_data_file = os.path.join(output_path, filename)
                    download_file(input_url, output_data_file)
                    break
            contents = my_file.readline()

    # Remove resources.csv:
    os.remove(output_file)

    # Concatenate data:

    # Get existing years in data/raw files:
    year_list = []
    for filename in os.listdir(path_data_raw):
        year = filename[-8:-4]
        if year not in year_list:
            year_list.append(year)

    # Merge files:
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

    # Paths to files:
    # input_filepath_users = os.path.join(path_data_interim, "usagers.csv")
    # input_filepath_caract = os.path.join(path_data_interim,
    # "caracteristiques.csv")
    # input_filepath_places = os.path.join(path_data_interim, "lieux.csv")
    # input_filepath_veh = os.path.join(path_data_interim, "vehicules.csv")

    # Preprocess data using main function from make_dataset.py:
    # root_path = "../"
    sys.path.append(os.path.join(root_path, "src", "data"))
    main(input_filepath=path_data_interim,
         output_filepath=path_data_preprocessed)


if __name__ == '__main__':
    UpdateData(year_list=[2019, 2020])
