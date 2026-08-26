import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
import os
import logging
from glob import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def detect_delimiter(file_path, encoding="utf-8"):
    """Détecte le délimiteur d'un fichier CSV en essayant plusieurs options"""
    delimiters = [";", ",", "\t", "|"]

    for delimiter in delimiters:
        try:
            df_test = pd.read_csv(
                file_path,
                sep=delimiter,
                encoding=encoding,
                nrows=2,
                on_bad_lines="skip",
            )
            if df_test.shape[1] > 1:
                return delimiter
        except:
            continue

    return ";"  # Default fallback


def join_datasets(input_filepath):
    """
    Fusionne les csv pour chaque type de données : usagers, caracteristiques, lieux et véhicules
    avec toutes les années disponibles dans data/raw

    Args:
        input_filepath (str): Chemin vers le dossier data/raw

    Returns:
        dict: Dictionnaire contenant 4 dataframes (usagers, caracteristiques, lieux, vehicules)
    """
    logger = logging.getLogger(__name__)

    # Dictionnaires pour stocker les dataframes
    dataframes = {"usagers": [], "caracteristiques": [], "lieux": [], "vehicules": []}

    # Récupérer tous les fichiers CSV du dossier
    csv_files = glob(os.path.join(input_filepath, "*.csv"))
    logger.info(f"Fichiers trouvés: {len(csv_files)}")

    # Traiter chaque fichier
    for file in csv_files:
        filename = os.path.basename(file).lower()
        logger.info(f"Traitement du fichier: {filename}")

        try:
            # Détecter le délimiteur automatiquement
            delimiter = detect_delimiter(file)
            logger.info(f"  - Délimiteur détecté: '{delimiter}'")

            # Charger le CSV avec le délimiteur détecté
            df = pd.read_csv(file, sep=delimiter, encoding="utf-8", on_bad_lines="skip")
            logger.info(f"  - {filename}: {df.shape[0]} lignes, {df.shape[1]} colonnes")

            # Classifier par type de données
            if "usager" in filename:
                dataframes["usagers"].append(df)
            elif (
                "caract" in filename or "carcteri" in filename
            ):  # Handle both 'caracteristiques' and 'carcteristiques' (typo)
                dataframes["caracteristiques"].append(df)
            elif "lieux" in filename or "lieu" in filename:
                dataframes["lieux"].append(df)
            elif "vehicule" in filename or "vehicul" in filename:
                dataframes["vehicules"].append(df)
            else:
                logger.warning(f"  - Fichier non classifié: {filename}")

        except Exception as e:
            logger.error(f"Erreur lors du chargement de {filename}: {str(e)}")

    # Fusionner les dataframes par type
    result = {}
    for data_type, dfs in dataframes.items():
        if dfs:
            result[data_type] = pd.concat(dfs, ignore_index=True)
            logger.info(
                f"✓ {data_type.capitalize()}: {result[data_type].shape[0]} lignes au total"
            )
        else:
            logger.warning(f"✗ Aucun fichier trouvé pour: {data_type}")
            result[data_type] = pd.DataFrame()

    return result


def process_data(dataframes, output_folderpath):
    """
    Transforme les dataframes et les sauvegarde dans le dossier de sortie.
    """
    logger = logging.getLogger(__name__)

    # Vérifier que tous les dataframes existent et ne sont pas vides
    required_keys = ["usagers", "caracteristiques", "vehicules", "lieux"]
    for key in required_keys:
        if key not in dataframes or dataframes[key].empty:
            logger.error(f"Erreur: Le dataframe '{key}' est manquant ou vide")
            return False

    logger.info("=== Début des transformations ===")

    try:
        df_users = dataframes["usagers"].copy()
        df_caract = dataframes["caracteristiques"].copy()
        df_veh = dataframes["vehicules"].copy()
        df_places = dataframes["lieux"].copy()

        # Transformations pour usagers
        logger.info("Transformation des données usagers...")
        if "Num_Acc" in df_users.columns:
            df_users["year_acc"] = (
                df_users["Num_Acc"].astype(str).apply(lambda x: x[:4]).astype(int)
            )
            if "an_nais" in df_users.columns:
                df_users["victim_age"] = df_users["year_acc"] - df_users["an_nais"]
                df_users["victim_age"] = df_users["victim_age"].where(
                    (df_users["victim_age"] >= 0) & (df_users["victim_age"] <= 120),
                    np.nan,
                )
                df_users.drop(["an_nais"], inplace=True, axis=1)
            logger.info(f"  ✓ Colonnes créées: year_acc, victim_age")

        # Transformations pour caract
        logger.info("Transformation des données caractéristiques...")
        if "hrmn" in df_caract.columns:
            df_caract["hour"] = df_caract["hrmn"].astype(str).apply(lambda x: x[:-3])
            cols_to_drop = [col for col in ["hrmn", "an"] if col in df_caract.columns]
            df_caract.drop(cols_to_drop, inplace=True, axis=1)

        if "agg" in df_caract.columns:
            df_caract.rename({"agg": "agg_"}, inplace=True, axis=1)

        # Remplacer les codes Corse
        if "dep" in df_caract.columns:
            df_caract["dep"] = df_caract["dep"].astype(str).str.replace("2A", "201")
            df_caract["dep"] = df_caract["dep"].astype(str).str.replace("2B", "202")
        if "com" in df_caract.columns:
            df_caract["com"] = df_caract["com"].astype(str).str.replace("2A", "201")
            df_caract["com"] = df_caract["com"].astype(str).str.replace("2B", "202")

        # Convertir les types
        cols_int = [col for col in ["dep", "com", "hour"] if col in df_caract.columns]
        if cols_int:
            # Replace 'N/C' and other non-numeric values with NaN before converting
            for col in cols_int:
                df_caract[col] = pd.to_numeric(df_caract[col], errors="coerce")
            df_caract[cols_int] = df_caract[cols_int].fillna(0).astype(int)

        # Convertir lat/long
        if "lat" in df_caract.columns:
            df_caract["lat"] = df_caract["lat"].astype(str).str.replace(",", ".")
            df_caract["lat"] = pd.to_numeric(df_caract["lat"], errors="coerce")
        if "long" in df_caract.columns:
            df_caract["long"] = df_caract["long"].astype(str).str.replace(",", ".")
            df_caract["long"] = pd.to_numeric(df_caract["long"], errors="coerce")

        # Regrouper les modalités
        if "atm" in df_caract.columns:
            dico_atm = {1: 0, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 0, 9: 0}
            df_caract["atm"] = df_caract["atm"].replace(dico_atm)

        logger.info(f"  ✓ Transformations effectuées")

        # Transformations pour véhicules
        logger.info("Transformation des données véhicules...")
        if "Num_Acc" in df_veh.columns:
            nb_vehicules = (
                df_veh.groupby("Num_Acc").size().reset_index(name="nb_vehicules")
            )

        if "catv" in df_veh.columns:
            catv_value = [
                0,
                1,
                2,
                3,
                4,
                5,
                6,
                7,
                8,
                9,
                10,
                11,
                12,
                13,
                14,
                15,
                16,
                17,
                18,
                19,
                20,
                21,
                30,
                31,
                32,
                33,
                34,
                35,
                36,
                37,
                38,
                39,
                40,
                41,
                42,
                43,
                50,
                60,
                80,
                99,
            ]
            catv_value_new = [
                0,
                1,
                1,
                2,
                1,
                1,
                6,
                2,
                5,
                5,
                5,
                5,
                5,
                4,
                4,
                4,
                4,
                4,
                3,
                3,
                4,
                4,
                1,
                1,
                1,
                1,
                1,
                6,
                6,
                3,
                3,
                3,
                3,
                1,
                1,
                1,
                1,
                1,
                0,
                0,
            ]
            catv_mapping = dict(zip(catv_value, catv_value_new))
            df_veh["catv"] = df_veh["catv"].replace(catv_mapping)

        logger.info(f"  ✓ Regroupement des modalités effectué")

        # Compter les victimes
        if "Num_Acc" in df_users.columns:
            nb_victim = df_users.groupby("Num_Acc").size().reset_index(name="nb_victim")

        logger.info("Fusion des dataframes...")
        # Fusionner les datasets
        merge_cols = [
            col
            for col in ["Num_Acc", "num_veh", "id_vehicule"]
            if col in df_users.columns and col in df_veh.columns
        ]
        if len(merge_cols) >= 1:
            fusion1 = df_users.merge(df_veh, on=merge_cols, how="inner")
        else:
            fusion1 = df_users

        if "grav" in fusion1.columns:
            # Modifier la variable cible
            fusion1["grav"] = fusion1["grav"].replace([2, 4], [4, 2])  # Inverser les valeurs 2 et 4
            # Garder la ligne avec la gravité la plus sévère pour chaque accident
            fusion1 = fusion1.sort_values(by="grav", ascending=False)
        if "Num_Acc" in fusion1.columns:
            fusion1 = fusion1.drop_duplicates(subset=["Num_Acc"], keep="first")

        if "Num_Acc" in fusion1.columns and "Num_Acc" in df_places.columns:
            fusion2 = fusion1.merge(df_places, on="Num_Acc", how="left")
        else:
            fusion2 = fusion1

        if "Num_Acc" in fusion2.columns and "Num_Acc" in df_caract.columns:
            df = fusion2.merge(df_caract, on="Num_Acc", how="left")
        else:
            df = fusion2

        # Ajouter les nouvelles colonnes
        if "Num_Acc" in df.columns and "Num_Acc" in nb_victim.columns:
            df = df.merge(nb_victim, on="Num_Acc", how="inner")
        if "Num_Acc" in df.columns and "Num_Acc" in nb_vehicules.columns:
            df = df.merge(nb_vehicules, on="Num_Acc", how="inner")

        logger.info(f"  ✓ Fusion effectuée: {df.shape[0]} lignes")

        # Modifier la variable cible
        if "grav" in df.columns:
            df["grav"] = df["grav"].replace([1, 2, 3, 4], [0, 0, 1, 1]) # indemne (0), blessé léger (0), blessé hospitalisé (1), tué (1)
            # df["grav"] = df["grav"].replace([1, 2, 3, 4], [0, 1, 1, 1]) # indemne (0), blessé léger (1), blessé hospitalisé (1), tué (1)

        # Remplacer les valeurs -1 et 0 par NaN
        col_to_replace0_na = ["trajet", "catv", "motor"]
        col_to_replace1_na = [
            "trajet",
            "secu1",
            "catv",
            "obsm",
            "motor",
            "circ",
            "surf",
            "situ",
            "vma",
            "atm",
            "col",
        ]

        for col in col_to_replace1_na:
            if col in df.columns:
                df[col] = df[col].replace(-1, np.nan)
        for col in col_to_replace0_na:
            if col in df.columns:
                df[col] = df[col].replace(0, np.nan)

        # Supprimer les colonnes non nécessaires
        list_to_drop = [
            "senc",
            "larrout",
            "actp",
            "manv",
            "choc",
            "nbv",
            "prof",
            "plan",
            "Num_Acc",
            "id_vehicule",
            "num_veh",
            "pr",
            "pr1",
            "voie",
            "trajet",
            "secu2",
            "secu3",
            "adr",
            "v1",
            "lartpc",
            "occutc",
            "v2",
            "vosp",
            "locp",
            "etatp",
            "infra",
            "obs",
        ]
        columns_to_drop = [col for col in list_to_drop if col in df.columns]
        df.drop(columns_to_drop, axis=1, inplace=True)
        logger.info(f"  ✓ Colonnes supprimées: {len(columns_to_drop)}")

        # Supprimer les lignes avec NaN
        col_to_drop_lines = ["catv", "vma", "secu1", "obsm", "atm"]
        col_to_drop_lines_filtered = [
            col for col in col_to_drop_lines if col in df.columns
        ]
        if col_to_drop_lines_filtered:
            df = df.dropna(subset=col_to_drop_lines_filtered, axis=0)
        logger.info(f"  ✓ Lignes avec NaN supprimées. Reste: {df.shape[0]} lignes")

        if "grav" not in df.columns:
            logger.error("La colonne 'grav' n'existe pas dans le dataframe final")
            return False

        target = df["grav"]
        feats = df.drop(["grav"], axis=1)

        # Sauvegarde du dataset complet prétraité à la racine du dossier data
        root_data_path = os.path.join(os.getcwd(), "data/preprocessed")
        os.makedirs(root_data_path, exist_ok=True)
        
        output_final_df = os.path.join(root_data_path, "preprocessed.csv")
        df.to_csv(output_final_df, index=False)
        logger.info(f"✓ Dataset complet sauvegardé : {output_final_df} ({df.shape[0]} lignes)")

        # On retire les colonnes qui sont des identifiants et non des features
        cols_to_drop = ["id_usager", "Accident_Id"]
        # On utilise .intersection() pour éviter une erreur si la colonne n'existe pas déjà
        cols_to_drop = [c for c in cols_to_drop if c in feats.columns]

        if cols_to_drop:
            feats = feats.drop(columns=cols_to_drop)
            logger.info(
                f"  ✓ Colonnes identifiants retirées des features: {cols_to_drop}"
            )

        logger.info(f"Séparation train/test...")
        X_train, X_test, y_train, y_test = train_test_split(
            feats, target, test_size=0.3, random_state=42
        )
        logger.info(f"  ✓ Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")

        # Remplir les NaN
        col_to_fill_na = ["surf", "circ", "col", "motor"]
        col_to_fill_na_filtered = [
            col for col in col_to_fill_na if col in X_train.columns
        ]

        if col_to_fill_na_filtered:
            for col in col_to_fill_na_filtered:
                X_train[col] = X_train[col].fillna(
                    X_train[col].mode().iloc[0] if len(X_train[col].mode()) > 0 else 0
                )
                X_test[col] = X_test[col].fillna(
                    X_train[col].mode().iloc[0] if len(X_train[col].mode()) > 0 else 0
                )
            logger.info(f"  ✓ NaN remplis pour: {col_to_fill_na_filtered}")

        # Créer le dossier de sortie
        os.makedirs(output_folderpath, exist_ok=True)

        logger.info(f"Sauvegarde des données...")
        for file, filename in zip(
            [X_train, X_test, y_train, y_test],
            ["X_train", "X_test", "y_train", "y_test"],
        ):
            output_filepath = os.path.join(output_folderpath, f"{filename}.csv")
            file.to_csv(output_filepath, index=False)
            logger.info(f"  ✓ {filename}.csv sauvegardé ({file.shape[0]} lignes)")

        logger.info("=== Traitement terminé avec succès ===\n")
        return True

    except Exception as e:
        logger.error(f"Erreur lors du traitement: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return False


def main(input_filepath=None, output_filepath=None):
    """Exécute le traitement des données"""
    logger = logging.getLogger(__name__)
    logger.info("making final data set from raw data")

    input_filepath = input_filepath or os.path.join(os.getcwd(), "data", "raw")
    output_filepath = output_filepath or os.path.join(
        os.getcwd(), "data", "preprocessed"
    )

    logger.info(f"Chemin d'entrée: {input_filepath}")
    logger.info(f"Chemin de sortie: {output_filepath}")

    os.makedirs(output_filepath, exist_ok=True)

    logger.info("Fusion des fichiers CSV par type de données...")
    dataframes = join_datasets(input_filepath)

    logger.info("\n=== Résumé des données chargées ===")
    for data_type, df in dataframes.items():
        if not df.empty:
            logger.info(
                f"{data_type.capitalize()}: {df.shape[0]} lignes × {df.shape[1]} colonnes"
            )
        else:
            logger.warning(f"{data_type.capitalize()}: VIDE")

    # Check if all dataframes are loaded (not empty)
    if not all(not df.empty for df in dataframes.values()):
        logger.error(
            "Erreur: Un ou plusieurs types de données n'ont pas pu être chargés"
        )
        return None

    logger.info("")
    success = process_data(dataframes, output_filepath)

    return dataframes if success else None


if __name__ == "__main__":
    input_path = "data/raw"
    output_path = "data/preprocessed"

    result = main(input_path, output_path)

    if result:
        print("\n=== DataFrames chargés ===")
        for data_type, df in result.items():
            if not df.empty:
                print(f"\n{data_type.upper()} - Shape: {df.shape}")
