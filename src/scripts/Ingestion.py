# Import des bibliothèques nécessaires au projet
import pandas as pd
import numpy as np
import warnings


# Ignorer les avertissements
warnings.filterwarnings("ignore", category=pd.errors.DtypeWarning)

#créer une fonction d'ingestion de data
def load_data(file_path,encoding=None, index_col=None):
    
    df = pd.read_csv(file_path, encoding=encoding, index_col=index_col)

    return df

#créer des fonctions pour nettoyer les data


def clean_lieux(df):
    # au vue du nombre de valeurs manquantes, nous pouvons supprimer : voie, v1, v2, pr, pr1, env1, vma
    colonnes_a_supprimer = ['voie','v1', 'v2', 'pr', 'pr1', 'env1', 'vma']
    df = df.drop(columns=colonnes_a_supprimer, axis=1)
    # uniformisation du type de données parmi tous les dataframes
    a_convertir = ['catr', 'circ', 'nbv', 'vosp', 'prof', 'plan', 'lartpc', 'larrout', 'surf', 'infra', 'situ']
    df[a_convertir] = df[a_convertir].fillna(0).astype('int64')
    # afin de permettre la fusion ultérieure des dataframes, on supprime la colonne commune 'annee' que nous laisserons dans df_usagers
    df = df.drop(columns=['annee'], axis=1)
    return df

def clean_carac(df):
    # au vue du nombre de valeurs manquantes, nous pouvons supprimer : adr, gps, lat, long
    colonnes_a_supprimer = ['adr', 'gps', 'lat', 'long']
    df = df.drop(columns=colonnes_a_supprimer, axis=1)
    # on encode les variables le nécessitant
    df['dep'] = df['dep'].replace({'2A': 1000, '2B': 1001})
    # on supprime les données qui ne sont pas entières (bien que leur format laisse à penser que 'dep' et 'com' ont été fusionnés)
    def filter_non_int(com):
        try:
            return int(com)
        except ValueError:
            return None
    df['com'] = df['com'].apply(filter_non_int)
    # on distingue les heures et les minutes
    df[['hr', 'mn']] = df['hrmn'].str.extract(r'(\d{2})(\d{2})')
    df.drop('hrmn', axis=1, inplace=True)
    # uniformisation du type de données parmi tous les dataframes
    a_convertir = ['atm', 'col', 'dep', 'com', 'hr', 'mn']
    df[a_convertir] = df[a_convertir].fillna(0).astype('int64')
    # afin de permettre la fusion ultérieure des dataframes, on supprime la colonne commune 'annee' que nous laisserons dans df_usagers
    df = df.drop(columns=['annee'], axis=1)
    return df

def clean_usagers(df):
    # au vue du nombre de valeurs manquantes, nous pouvons supprimer :
    colonnes_a_supprimer = ["id_vehicule", "secu1", "secu2", "secu3", "secu"]
    df = df.drop(columns=colonnes_a_supprimer, axis=1)
    # on encode les variables le nécessitant
    df['actp'] = df['actp'].replace({'A': 10, 'B': -1})
    # uniformisation du type de données parmi tous les dataframes
    a_convertir = ['num_acc', 'place', 'trajet', 'locp', 'actp', 'etatp', 'an_nais']
    df[a_convertir] = df[a_convertir].fillna(0).astype('int64')
    # les colonnes catu ne peuvent pas intégrer la valeur '4'
    # les colonnes sans la valeur cible du projet 'grav' renseignée n'ont aucune utilité, nous les supprimons donc
    condition = (df['catu'] == 4) | (df['grav'] == -1)
    df.drop(df[condition].index, inplace=True)
    # on rassemble les blessés de type 4 avec les personnes indemne
    df['grav'] = df['grav'].replace({4: 1})
    return df


def clean_vehicules(df):
    # au vue du nombre de valeurs manquantes, nous pouvons supprimer :
    colonnes_a_supprimer = ['occutc', 'id_vehicule', 'motor']
    df.drop(columns=colonnes_a_supprimer, inplace=True)
    # uniformisation du type de données parmi tous les dataframes
    a_convertir = ['senc', 'obs', 'obsm', 'choc', 'manv']
    df[a_convertir] = df[a_convertir].fillna(0).astype('int64')
    # afin de permettre la fusion ultérieure des dataframes, on supprime la colonne commune 'annee' que nous laisserons dans df_usagers
    df = df.drop(columns=['annee'], axis=1)
    return df

#création d'une fonction pour fusionner les dataframes
def merge_datasets(df_carac, df_vehicules, df_usagers, df_lieux):
    df = pd.merge(df_carac, df_vehicules, on='num_acc', how="inner")
    df = pd.merge(df, df_usagers, on=["num_acc","num_veh"], how='inner')
    df = pd.merge(df, df_lieux, on='num_acc', how='inner')
    return df



def clean_data(df):
    # on transforme les -1 et 0 en NaN (signification identique)
    colonne_Non_cat = ['num_acc', 'an_nais', "num_veh_x", 'annee', "num_veh_y", 'mois', 'jour', 'com', 'dep', 'hr', 'mn','nbv','lartpc','larrout']
    cat_columns = [col for col in df.columns if col not in colonne_Non_cat]
    df[cat_columns] = df[cat_columns].replace({-1: np.nan})
    # au vue du nombre de valeurs manquantes, nous pouvons supprimer :
    colonnes_a_supprimer = ['locp', 'actp', 'etatp', 'senc', 'obs', 'obsm', 'vosp', 'infra']
    df = df.drop(columns=colonnes_a_supprimer)
    # on supprime désormais les lignes avec des NaN (ne pouvant les remplacer par d'autres catégories de façon aléatoire)
    df_cleaned = df.dropna()
    # colonne non catégorielle
    colonne_Non_cat=['num_acc', 'an_nais', "num_veh", 'annee', 'mois', 'jour', 'com', 'dep', 'hr', 'mn','nbv','lartpc','larrout']

    # colonne catégorielle
    cat_columns = [col for col in df_cleaned.columns if col not in colonne_Non_cat]

    # Calculer les  correlations des variables categoricalles
    #cat_corr = calculate_categorical_correlations(df_cleaned, cat_columns)

    #print("Chi2 avec 'grav':")
    #print(cat_corr)

    # supprimer les variables atm, annee_y, annee_x, sexe et surf ne semblent pas corrélées avec grav 
    colonnes_a_supprimer = ['atm', 'annee', 'sexe', 'surf', "num_veh"]
    df_cleaned = df_cleaned.drop(columns=colonnes_a_supprimer)
    return df_cleaned

def save_cleaned_data(df, file_path):
    df.to_csv(file_path, index=False)

# etape supplémentaire pour réduire le jeu de données (et pouvoir le déposer sur github)
def select_sample(file_path,final_file_path):
    df = pd.read_csv(file_path)
    print(df['grav'].value_counts())
    total_lignes = 50000 
    colonne_classe = 'grav'  
    # on vérifie que le nombre de lignes par classe en fonction des proportions existantes est égal car le jeu de données a fait l objet d un undersampling au préalable
    prop_classes = df['grav'].value_counts(normalize=True)
    lignes_par_classe = (prop_classes * total_lignes).astype(int)
    df_final = pd.DataFrame()
    for classe, n in lignes_par_classe.items():
        df_classe = df[df['grav'] == classe].sample(n=n, random_state=42)
        df_final = pd.concat([df_final, df_classe])
    print(df_final['grav'].value_counts())
    #df_final.to_csv(final_file_path,index=False)
    return df_final



def main():

 # Load datasets
    df_lieux = load_data('../data/lieux_2005a2021.csv', index_col=0)
    df_carac = load_data('../data/caracteristiques_2005a2021.csv', encoding='iso-8859-1', index_col=0)
    df_usagers = load_data('../data/usagers_2005a2021.csv', index_col=0)
    df_vehicules = load_data('../data/vehicules_2005a2021.csv', index_col=0)

    # Preprocess datasets
    df_lieux = clean_lieux(df_lieux)
    df_carac = clean_carac(df_carac)
    df_usagers =clean_usagers(df_usagers)
    df_vehicules = clean_vehicules(df_vehicules)

    # Merge datasets
    df_merged = merge_datasets(df_carac, df_vehicules, df_usagers, df_lieux)

    # Clean merged dataset
    df_cleaned = clean_data(df_merged)
    print(len(df_cleaned))

    # Save cleaned dataset
    #save_cleaned_data(df_cleaned, '../data/data_2005a2021.csv')

    file_path="../data/data_2005a2021.csv"
    final_file_path="../data/data_2005a2021_final.csv"
    df_final=select_sample(file_path,final_file_path)
    
if __name__ == "__main__":
    main()
    
