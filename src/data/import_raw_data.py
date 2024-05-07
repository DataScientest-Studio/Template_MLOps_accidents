import requests
import os
import logging
import shutil
from pathlib import Path


# S3 url:
s3_url = "https://mlops-project-db.s3.eu-west-1.amazonaws.com/accidents/"

# paths:
root_path = Path(os.path.realpath(__file__)).parents[2]
path_data_raw = os.path.join(root_path, "data", "raw")
path_data_interim = os.path.join(root_path, "data", "interim")


# --------------- import_raw_data ---------------------------------------------
def import_raw_data(raw_data_relative_path,
                    interim_data_relative_path,
                    filenames,
                    bucket_folder_url):
    '''import filenames from bucket_folder_url in raw_data_relative_path'''

    # download all the files
    for filename in filenames:
        input_file = os.path.join(bucket_folder_url, filename)
        output_file = os.path.join(raw_data_relative_path, filename)
        object_url = input_file
        print(f'downloading {input_file} as {os.path.basename(output_file)}')
        response = requests.get(object_url)
        if response.status_code == 200:
            # Process the response content as needed
            content = response.text
            text_file = open(output_file, "wb")
            text_file.write(content.encode('utf-8'))
            text_file.close()
        else:
            print(f'Error accessing the object {input_file}:',
                  response.status_code)

    # Rename and move to ./data/interim:
    for filename in filenames:
        src = os.path.join(raw_data_relative_path, f"{filename}")
        dest = os.path.join(interim_data_relative_path, f"{filename[:-9]}.csv")
        shutil.copyfile(src, dest)


# --------------- main ---------------------------------------------
def main(raw_data_relative_path=path_data_raw,
         interim_data_relative_path=path_data_interim,
         filenames=["caracteristiques-2021.csv", "lieux-2021.csv",
                    "usagers-2021.csv", "vehicules-2021.csv"],
         bucket_folder_url=s3_url
         ):
    """ Upload data from AWS s3 in ./data/raw
    """
    import_raw_data(raw_data_relative_path,
                    interim_data_relative_path,
                    filenames,
                    bucket_folder_url)
    logger = logging.getLogger(__name__)
    logger.info('making raw data set')


if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    main()
