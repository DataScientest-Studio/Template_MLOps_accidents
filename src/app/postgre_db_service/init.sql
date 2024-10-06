-- Créer la table donnees_accidents
CREATE TABLE IF NOT EXISTS donnees_accidents (
    num_acc BIGINT PRIMARY KEY,
    mois INT,
    jour INT,
    lum INT,
    agg INT,
    int INT,
    col FLOAT,
    com INT,
    dep INT,
    hr INT,
    mn INT,
    catv INT,
    choc FLOAT,
    manv FLOAT,
    place INT,
    catu INT,
    grav INT,
    trajet FLOAT,
    an_nais INT,
    catr INT,
    circ FLOAT,
    nbv INT,
    prof FLOAT,
    plan FLOAT,
    lartpc INT,
    larrout INT,
    situ FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_ref VARCHAR(3) DEFAULT 'yes'
);

-- Créer la table predictions_accidents
CREATE TABLE IF NOT EXISTS predictions_accidents (
    num_acc BIGINT PRIMARY KEY,
    mois INT,
    jour INT,
    lum INT,
    agg INT,
    int INT,
    col FLOAT,
    com INT,
    dep INT,
    hr INT,
    mn INT,
    catv INT,
    choc FLOAT,
    manv FLOAT,
    place INT,
    catu INT,
    grav FLOAT, -- Notez le type FLOAT pour grav pour les prédictions
    trajet FLOAT,
    an_nais INT,
    catr INT,
    circ FLOAT,
    nbv INT,
    prof FLOAT,
    plan FLOAT,
    lartpc INT,
    larrout INT,
    situ FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_ref VARCHAR(3) DEFAULT 'no'
);

-- Créer une table temporaire pour l'importation des données
CREATE TEMP TABLE temp_donnees_accidents (
    num_acc BIGINT,
    mois INT,
    jour INT,
    lum INT,
    agg INT,
    int INT,
    col FLOAT,
    com INT,
    dep INT,
    hr INT,
    mn INT,
    catv INT,
    choc FLOAT,
    manv FLOAT,
    place INT,
    catu INT,
    grav INT,
    trajet FLOAT,
    an_nais INT,
    catr INT,
    circ FLOAT,
    nbv INT,
    prof FLOAT,
    plan FLOAT,
    lartpc INT,
    larrout INT,
    situ FLOAT
);

-- Charger les données CSV dans la table temporaire
COPY temp_donnees_accidents
FROM '/docker-entrypoint-initdb.d/data_2005a2021_final.csv'
DELIMITER ','
CSV HEADER;

-- Insérer les données distinctes dans la table finale, avec les nouvelles colonnes remplies
INSERT INTO donnees_accidents (
    num_acc, mois, jour, lum, agg, int, col, com, dep, hr, mn, catv, choc, manv, place, catu, grav, trajet, an_nais, catr, circ, nbv, prof, plan, lartpc, larrout, situ
)
SELECT DISTINCT ON (num_acc) 
    num_acc, mois, jour, lum, agg, int, col, com, dep, hr, mn, catv, choc, manv,place, catu, grav, trajet, an_nais, catr, circ, nbv, prof, plan, lartpc, larrout, situ
FROM temp_donnees_accidents
ON CONFLICT (num_acc) DO NOTHING;

-- Mettre à jour la colonne timestamp pour toutes les lignes avec l'heure du chargement
UPDATE donnees_accidents
SET timestamp = CURRENT_TIMESTAMP;
