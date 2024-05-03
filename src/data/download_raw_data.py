# import csv
import os
import requests
# import shutil


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


def download_raw_data(year_list):
    if (2021 or 2022) in year_list:
        print("Erreur: 2021 ou 2022 ne doivent pas être dans la liste des \
              années demandées, sous peine d'effacer les données fournies par \
              datascientest, ou d'ajouter des données problématiques.\n \
              Veuillez retirer cette année de votre liste.")

    else:
        output_path = "../../data/raw"
        http_url = "https://www.data.gouv.fr/fr/datasets/r/"

        # download list of ressources from gouv.fr
        output_file = os.path.join(output_path, "ressources.csv")
        download_file("https://www.data.gouv.fr/resources.csv", output_file)

        # download data files according to the year list
        file_list_template = ["carcteristiques", "caracteristiques", "lieux",
                              "usagers", "vehicules"]
        data_files_list = [f'{item}-{year}.csv' for item in file_list_template
                           for year in year_list]

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

        # patches
        for filename in os.listdir(output_path):
            if "carcteristiques" in filename:
                # patch caracteristiques filename
                year = filename[-8:-4]
                src_file = os.path.join(output_path, filename)
                dest_file = os.path.join(output_path,
                                         f"caracteristiques-{year}.csv")
                os.rename(src_file, dest_file)

# DELETE mais en ciblant davantage:
#        # patch usagers file : remove 2nd column
#        src = os.path.join(output_path, f"usagers-{year}.csv")
#        dest = os.path.join(output_path, f"_usagers-{year}.csv")
#        shutil.copyfile(src, dest)
#        with open(dest, "r") as source:
#            rdr= csv.reader(source, delimiter=';')
#            with open(src, "w") as result:
#                wtr= csv.writer(result, delimiter=";", quoting=csv.QUOTE_ALL)
#                for r in rdr:
#                    if r:
#                        del r[1]  # 2nd column
#                        wtr.writerow(r)

# Pas nécessaire car concerne seulement 2022:
        # RENAME: La colonne {'Num_Acc'} du dataset caracteristiques de
        #  datascientest s'intitule {'Accident_Id'} dans le dataset du
        # gouvernement de 2022 .
        # DELETE: Le dataset "lieux" en 2022 a un problème de mixed types dans
        # la colonne 6 intitulée 'nbv': a supprimer.


if __name__ == "__main__":
    # Ne pas mettre 2021 pour ne pas effacer les données fournies
    # par datascientest:
    # Ne pas mettre 2022 car il y a beaucoup plus de travail de data quality
    # que prévu.
    download_raw_data([2019, 2020])
