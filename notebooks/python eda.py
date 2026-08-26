import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import logging

# Configuration du style pour des graphiques propres
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_data(filepath):
    """Charge le dataset et vérifie sa structure de base."""
    if not os.path.exists(filepath):
        logger.error(f"Le fichier {filepath} n'existe pas.")
        return None
    
    logger.info(f"Chargement des données depuis {filepath}...")
    try:
        df = pd.read_csv(filepath)
        logger.info(f"✓ Dataset chargé : {df.shape[0]} lignes, {df.shape[1]} colonnes")
        return df
    except Exception as e:
        logger.error(f"Erreur lors du chargement : {e}")
        return None

def check_unique_accidents(df, id_col='Num_Acc', output_dir='references/figures'):
    """Vérifie le ratio entre le nombre de lignes et le nombre d'accidents uniques."""
    logger.info("--- Vérification de l'unité d'analyse (Accidents Uniques) ---")
    
    if id_col not in df.columns:
        logger.warning(f"La colonne identifiant '{id_col}' n'est pas trouvée. Impossible de vérifier les doublons d'accidents.")
        return

    total_rows = len(df)
    unique_accidents = df[id_col].nunique()
    
    if unique_accidents == 0:
        logger.warning("Aucun accident unique trouvé.")
        return

    ratio = total_rows / unique_accidents

    logger.info(f"Nombre total de lignes (usagers/véhicules) : {total_rows}")
    logger.info(f"Nombre d'accidents uniques ({id_col}) : {unique_accidents}")
    logger.info(f"Ratio moyen : {ratio:.2f} lignes par accident")
    
    if ratio > 1.5:
        logger.warning("⚠️  ATTENTION : Ratio élevé détecté.")
        logger.warning("Cela signifie qu'un accident moyen implique plusieurs lignes (victimes/véhicules).")
        logger.warning("⚠️  RISQUE : Une séparation Train/Test aléatoire classique créera une FUITE DE DONNÉES (Data Leakage).")
        logger.warning("→ Solution : Il faudra grouper par 'Num_Acc' avant le split, ou utiliser un GroupKFold.")
    
    # Distribution du nombre de victimes par accident
    plt.figure(figsize=(10, 6))
    victim_counts = df.groupby(id_col).size()
    
    # Sécurisation des bins pour éviter les erreurs si max est très grand
    max_val = int(victim_counts.max()) + 2
    bins = range(1, max_val)
    
    sns.histplot(victim_counts, bins=bins, kde=False, color="salmon")
    plt.title(f"Distribution du nombre de lignes par accident ({id_col})")
    plt.xlabel("Nombre de lignes (victimes/véhicules) par accident")
    plt.ylabel("Nombre d'accidents")
    
    # Affiche les ticks tous les 1 ou 2 ou 5 selon la taille pour ne pas surcharger
    step = max(1, max_val // 20) 
    plt.xticks(range(1, max_val, step))
    
    # Utilisation de output_dir pour être cohérent avec le reste du script
    save_plot(f"{output_dir}/00_distribution_accidents_uniques.png")
    plt.close()
    
    logger.info(f"✓ Graphique de distribution sauvegardé dans {output_dir}/00_distribution_accidents_uniques.png")

def analyze_target(df, target_col='grav', output_dir='references/figures'):
    """Étape 1 : Analyse de la distribution de la cible."""
    logger.info("--- Étape 1 : Analyse de la cible (grav) ---")
    
    if target_col not in df.columns:
        logger.warning(f"La colonne cible '{target_col}' n'est pas présente.")
        return

    dist = df[target_col].value_counts(normalize=True) * 100
    logger.info("Distribution de la cible (en %):")
    logger.info(f"\n{dist.round(2)}")

    plt.figure(figsize=(8, 6))
    ax = sns.countplot(data=df, x=target_col, palette="viridis")
    plt.title(f"Distribution de la variable cible : {target_col}")
    plt.xlabel("Classe (0: Indemne/Léger, 1: Grave/Tué)")
    plt.ylabel("Nombre d'accidents")
    
    for p in ax.patches:
        height = p.get_height()
        ax.text(p.get_x() + p.get_width()/2., height + 0.5,
                f'{height/len(df)*100:.1f}%', ha="center", fontsize=11)
    
    save_plot(f"{output_dir}/01_distribution_cible.png")
    plt.close()

def analyze_missing_values(df, output_dir='references/figures'):
    """Étape 2 : Analyse des valeurs manquantes."""
    logger.info("--- Étape 2 : Analyse des valeurs manquantes ---")
    
    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100
    missing_df = pd.DataFrame({'Nombre': missing, 'Pourcentage': missing_pct})
    missing_df = missing_df[missing_df['Nombre'] > 0].sort_values('Pourcentage', ascending=False)
    
    if missing_df.empty:
        logger.info("✓ Aucune valeur manquante détectée.")
        return
    
    logger.info("Colonnes avec valeurs manquantes :")
    logger.info(f"\n{missing_df.round(2)}")

    plt.figure(figsize=(12, 8))
    sns.barplot(x=missing_df['Pourcentage'], y=missing_df.index, palette="magma")
    plt.title("Pourcentage de valeurs manquantes par colonne")
    plt.xlabel("Pourcentage (%)")
    plt.ylabel("Colonnes")
    plt.xlim(0, 100)
    
    save_plot(f"{output_dir}/02_valeurs_manquantes.png")
    plt.close()

def analyze_descriptive_stats(df, output_dir='references/figures'):
    """Étape 3 : Statistiques descriptives séparées par type."""
    logger.info("--- Étape 3 : Statistiques descriptives ---")
    
    num_cols = df.select_dtypes(include=[np.number]).columns
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    
    logger.info(f"Variables numériques trouvées : {len(num_cols)}")
    logger.info(f"Variables catégorielles trouvées : {len(cat_cols)}")
    
    if len(num_cols) > 0:
        logger.info("\n--- Résumé variables numériques ---")
        logger.info(f"\n{df[num_cols].describe().round(2)}")
        
        cols_to_plot = num_cols[:12] 
        n_cols = 3
        n_rows = (len(cols_to_plot) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
        
        # Correction robuste pour gérer axes (scalaire, liste ou tableau)
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        for i, col in enumerate(cols_to_plot):
            sns.boxplot(y=df[col], ax=axes[i], color="skyblue")
            axes[i].set_title(f"Boxplot : {col}")
            axes[i].set_xlabel("")
        
        for j in range(i+1, len(axes)):
            fig.delaxes(axes[j])
            
        plt.tight_layout()
        save_plot(f"{output_dir}/03_boxplots_numeriques.png")
        plt.close()

    if len(cat_cols) > 0:
        logger.info("\n--- Aperçu variables catégorielles (Top 5 catégories) ---")
        for col in cat_cols[:5]: 
            logger.info(f"\nColonne : {col}")
            logger.info(f"{df[col].value_counts().head(5)}")

def analyze_univariate_relations(df, target_col='grav', output_dir='references/figures'):
    """Étape 4 : Relations univariées avec la cible."""
    logger.info("--- Étape 4 : Relations avec la cible ---")
    
    if target_col not in df.columns:
        return

    num_cols = df.select_dtypes(include=[np.number]).columns.drop(target_col, errors='ignore')
    cat_cols = df.select_dtypes(include=['object', 'category']).columns

    # 4a. Numérique vs Cible
    cols_to_plot = num_cols[:6] 
    if len(cols_to_plot) > 0:
        n_cols = 2
        n_rows = (len(cols_to_plot) + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 5*n_rows))
        
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        else:
            axes = axes.flatten()

        for i, col in enumerate(cols_to_plot):
            sns.boxplot(x=df[target_col], y=df[col], ax=axes[i], palette="coolwarm")
            axes[i].set_title(f"{col} par Gravité")
            axes[i].set_xlabel("Gravité")
            axes[i].set_ylabel(col)
        
        for j in range(i+1, len(axes)):
            fig.delaxes(axes[j])
        plt.tight_layout()
        save_plot(f"{output_dir}/04_numerique_vs_cible.png")
        plt.close()

    # 4b. Catégoriel vs Cible
    cols_to_plot = cat_cols[:6]
    if len(cols_to_plot) > 0:
        n_cols = 2
        n_rows = (len(cols_to_plot) + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 5*n_rows))
        
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        else:
            axes = axes.flatten()

        for i, col in enumerate(cols_to_plot):
            df_temp = df.groupby([col, target_col]).size().unstack(fill_value=0)
            df_temp_pct = df_temp.div(df_temp.sum(axis=1), axis=0) * 100
            
            df_temp_pct.plot(kind='bar', stacked=True, ax=axes[i], colormap="viridis", legend=i==0)
            axes[i].set_title(f"Répartition Gravité par {col}")
            axes[i].set_xlabel(col)
            axes[i].set_ylabel("Pourcentage (%)")
            if i != 0:
                axes[i].legend_.remove()
            axes[i].tick_params(axis='x', rotation=45)

        for j in range(i+1, len(axes)):
            fig.delaxes(axes[j])
        
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, title="Gravité", loc="upper right", bbox_to_anchor=(1, 1))
        
        plt.tight_layout()
        save_plot(f"{output_dir}/04_categoriel_vs_cible.png")
        plt.close()

def analyze_correlations(df, output_dir='references/figures'):
    """Étape 5 : Matrice de corrélation."""
    logger.info("--- Étape 5 : Matrice de corrélation ---")
    
    num_df = df.select_dtypes(include=[np.number])
    
    if num_df.shape[1] < 2:
        logger.info("Pas assez de variables numériques pour une corrélation.")
        return

    corr = num_df.corr()
    
    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap='coolwarm', vmin=-1, vmax=1, center=0)
    plt.title("Matrice de corrélation (Variables Numériques)")
    
    save_plot(f"{output_dir}/05_correlation_heatmap.png")
    plt.close()

def save_plot(filepath):
    """Sauvegarde le graphique en gérant la création du dossier."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    logger.info(f"✓ Graphique sauvegardé : {filepath}")

def main():
    data_path = os.path.join(os.getcwd(), "data", "preprocessed.csv")
    report_dir = os.path.join(os.getcwd(), "references/figures")
    
    os.makedirs(report_dir, exist_ok=True)
    
    df = load_data(data_path)
    if df is None:
        return
    
    # Appel corrigé avec le paramètre output_dir
    check_unique_accidents(df, output_dir=report_dir)

    analyze_target(df, output_dir=report_dir)
    analyze_missing_values(df, output_dir=report_dir)
    analyze_descriptive_stats(df, output_dir=report_dir)
    analyze_univariate_relations(df, output_dir=report_dir)
    analyze_correlations(df, output_dir=report_dir)
    
    logger.info("\n" + "="*40)
    logger.info("✅ Analyse EDA terminée avec succès !")
    logger.info(f"📂 Retrouvez tous les graphiques dans le dossier : {report_dir}")
    logger.info("="*40 + "\n")

if __name__ == "__main__":
    main()