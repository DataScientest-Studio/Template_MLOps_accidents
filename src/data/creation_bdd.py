import sqlite3
import pandas as pd


# Charger le fichier CSV
df = pd.read_csv("src/data/data_2005a2021_final.csv")

# création de la base de données SQLite 
connexion = sqlite3.connect('src/data/data_accident.db')  
cursor = connexion.cursor()

# Enregistrement du DataFrame dans la base de données SQLite
df.to_sql("accidents", connexion, if_exists='replace', index=False)

# Fermer la connexion
connexion.close()
print("Données ajoutées avec succès à la base de données SQLite!")