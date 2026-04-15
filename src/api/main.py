import os
import time
import joblib
import pandas as pd
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest

app = FastAPI(title="Accident ML API")

PREDICTION_COUNT = Counter(
    "accident_predictions_total",
    "Nombre total de prédictions effectuées"
)

PREDICTION_LATENCY = Histogram(
    "accident_prediction_latency_seconds",
    "Temps de réponse des prédictions en secondes"
)

MODEL_VERSION = Gauge(
    "accident_model_version",
    "Version du modèle en production"
)

MODEL_DIR = Path(os.path.dirname(__file__)).parent.parent / "models"
MODEL_PATH = "models/model.joblib"


FEATURES = [
    "place",
    "catu",
    "sexe",
    "secu1",
    "year_acc",
    "victim_age",
    "catv",
    "obsm",
    "motor",
    "catr",
    "circ",
    "surf",
    "situ",
    "vma",
    "jour",
    "mois",
    "lum",
    "dep",
    "com",
    "agg_",
    "int",
    "atm",
    "col",
    "lat",
    "long",
    "hour",
    "nb_victim",
    "nb_vehicules",
]


FEATURE_LABELS = [
    "Lieu de l’accident",
    "Catégorie d’usager",
    "Sexe de l’usager",
    "Dispositif de sécurité",
    "Année de l’accident",
    "Âge de la victime",
    "Catégorie du véhicule",
    "Obstacle mobile",
    "Motorisation",
    "Catégorie de route",
    "Régime de circulation",
    "État de la surface",
    "Situation de l’accident",
    "Vitesse maximale autorisée",
    "Jour du mois",
    "Mois",
    "Luminosité",
    "Département",
    "Code commune",
    "Agglomération",
    "Type d’intersection",
    "Conditions atmosphériques",
    "Type de collision",
    "Latitude",
    "Longitude",
    "Heure",
    "Nombre de victimes",
    "Nombre de véhicules",
]

CHOICES = {
    # Localisation (en / hors agglomération)
    # Réf. BAAC 2017 – "LOCALISATION" (en/hors agglo)
    "agg_": {
        1: "Hors agglomération",
        2: "En agglomération",
    },
    # Lumière
    # Réf. BAAC 2017 – "LUMIÈRE"
    "lum": {
        1: "Plein jour",
        2: "Crépuscule ou aube",
        3: "Nuit sans éclairage public",
        4: "Nuit avec éclairage public non allumé",
        5: "Nuit avec éclairage public allumé",
    },
    # Intersection
    # Réf. BAAC 2017 – "INTERSECTION"
    "int": {
        1: "Hors intersection",
        2: "Intersection en X",
        3: "Intersection en T",
        4: "Intersection en Y",
        5: "Carrefour à plus de 4 branches",
        6: "Giratoire",
        7: "Place",
        8: "Passage à niveau",
        9: "Autre",
    },
    # Conditions atmosphériques
    # Réf. BAAC 2017 – "CONDITION ATMOSPHÉRIQUE"
    "atm": {
        1: "Normales",
        2: "Pluie légère",
        3: "Pluie forte",
        4: "Neige - grêle",
        5: "Brouillard - fumée",
        6: "Vent fort - tempête",
        7: "Temps éblouissant",
        8: "Temps couvert",
        9: "Autre",
    },
    # Type de collision
    # Réf. BAAC (schéma usuel open data) – ordre/labels usuels
    "col": {
        1: "Deux véhicules - frontale",
        2: "Deux véhicules - par l’arrière",
        3: "Deux véhicules - par le côté",
        4: "Trois véhicules et plus – en chaîne",
        5: "Trois véhicules et plus – collisions multiples",
        6: "Autre collision",
        7: "Sans collision",
    },
    # Catégorie administrative de la route
    # Réf. BAAC 2017 – "CATÉGORIE ADMINISTRATIVE"
    "catr": {
        1: "Autoroute",
        2: "Route nationale (ou territoriale)",
        3: "Route départementale (ou provinciale)",
        4: "Voie communale",
        5: "Hors réseau public",
        6: "Parc de stationnement ouvert à la circulation publique",
        9: "Autre",
    },
    # Régime de circulation
    # Réf. BAAC 2017 – "RÉGIME DE CIRCULATION"
    "circ": {
        1: "À sens unique",
        2: "Bidirectionnelle",
        3: "À chaussées séparées",
        4: "Avec voies d’affectation variable",
    },
    # État de surface
    # Réf. BAAC 2017 – "ÉTAT DE SURFACE"
    "surf": {
        1: "Normale",
        2: "Mouillée",
        3: "Flaques",
        4: "Inondée",
        5: "Enneigée",
        6: "Boue",
        7: "Verglacée",
        8: "Corps gras - Huile",
    },
    # Situation de l’accident
    # Réf. BAAC 2017 – "SITUATION DE L’ACCIDENT"
    "situ": {
        1: "Sur chaussée",
        2: "Sur bande d’arrêt d’urgence",
        3: "Sur accotement",
        4: "Sur trottoir",
        5: "Sur piste/bande cyclable",
        6: "Sur autre voie (BAU, bande médiane...)",
        7: "Sur terre-plein central / refuge",
        8: "Sur parking / aire",
        9: "Autre",
    },
    # Obstacle mobile heurté
    # Réf. BAAC 2017 – "OBSTACLE MOBILE HEURTÉ"
    "obsm": {
        0: "Aucun",
        1: "Piéton",
        2: "Véhicule",
        4: "Véhicule sur rail",
        5: "Animal domestique",
        6: "Animal sauvage",
        9: "Autre",
    },
    # Catégorie d’usager
    # Réf. BAAC 2017 – "CATÉGORIE D’USAGER"
    "catu": {
        1: "Conducteur",
        2: "Passager",
        3: "Piéton",
    },
    # Sexe
    # Réf. BAAC 2017 – "SEXE"
    "sexe": {
        1: "Masculin",
        2: "Féminin",
    },
    # Place dans le véhicule (occupants)
    # Réf. BAAC 2017 – "PLACE DANS LE VÉHICULE"
    "place": {
        1: "Conducteur",
        2: "Passager avant droit",
        3: "Passager arrière gauche",
        4: "Passager arrière centre",
        5: "Passager arrière droit",
        6: "Autre place (minibus/TC/etc.)",
        9: "Sans objet / Non applicable",
    },
    # Type de motorisation
    # Réf. BAAC 2017 – "TYPE DE MOTORISATION"
    "motor": {
        1: "Thermique (essence/diesel)",
        2: "Hybride non rechargeable",
        3: "Hybride rechargeable",
        4: "Électrique",
        5: "GPL / GNV / autre gaz",
        9: "Non renseigné",
    },
    # Équipement de sécurité - utilisation (1er item)
    # Réf. BAAC 2017 – "ÉQUIPEMENT DE SÉCURITÉ - UTILISATION"
    # (Dans le BAAC, plusieurs items existent ;
    # ici on expose le plus courant pour un unique champ 'secu1')
    "secu1": {
        0: "Aucun équipement",
        1: "Ceinture",
        2: "Casque",
        3: "Dispositif enfant",
        4: "Gilet airbag",
        5: "Gants",
        6: "Gilet haute visibilité",
        7: "Autre",
        9: "Non renseigné",
    },
    # Catégorie de véhicule (sous-ensemble utile pour l’UI)
    # Réf. BAAC – “CATEGORIE DE VEHICULE”
    # (format BAAC 2007/2017 ; liste complète très longue)
    # -> N’hésite pas à l’étendre si besoin pour ton jeu.
    "catv": {
        1: "Bicyclette",
        2: "Cyclomoteur < 50 cm³",
        3: "Voiturette / quadricycle léger",
        7: "VL seul",
        10: "VU seul (≤ 3,5 t)",
        13: "PL (> 3,5 t) + remorque",
        14: "PL seul (> 7,5 t)",
        15: "Tracteur routier",
        16: "Tracteur routier + semi-remorque",
        17: "Transport en commun (autobus/autocar)",
        30: "Scooter < 50 cm³",
        31: "Motocyclette > 50 et ≤ 125 cm³",
        32: "Scooter > 50 et ≤ 125 cm³",
        33: "Motocyclette > 125 cm³",
        34: "Scooter > 125 cm³",
        60: "Autre véhicule",
        99: "Inconnu / Non renseigné",
    },
}


SAMPLE = [
    1,
    1,
    1,
    8.0,
    2021,
    46.0,
    2.0,
    2.0,
    1.0,
    7,
    2.0,
    1.0,
    1.0,
    90.0,
    18,
    11,
    1,
    45,
    45072,
    1,
    1,
    0.0,
    1.0,
    47.964066,
    1.927586,
    17,
    2,
    2,
]


MODEL = None
MODEL_INFO = {}


@app.on_event("startup")
def load_model():
    global MODEL, MODEL_INFO
    try:
        MODEL = joblib.load(MODEL_PATH)
        MODEL_INFO = {"loaded": True, "model": str(type(MODEL)), "path": MODEL_PATH}
        MODEL_VERSION.set(1)
    except Exception as e:
        MODEL_INFO = {"loaded": False, "error": str(e)}


# ------------------------------------------------------------
# HEALTHCHECK
# ------------------------------------------------------------
@app.get("/health")
def healthz():
    return MODEL_INFO

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
# ------------------------------------------------------------
# PREDICT (JSON brut)
# ------------------------------------------------------------
@app.post("/predict")
async def predict(request: Request):
    start_time = time.time()

    if not MODEL_INFO.get("loaded"):
        return JSONResponse({"error": "model not loaded"}, status_code=500)

    try:
        data = await request.json()

        missing = [f for f in FEATURES if f not in data]
        if missing:
            return JSONResponse(
                {"error": f"missing features: {missing}"}, status_code=400
            )

        row = {}
        for f in FEATURES:
            try:
                row[f] = float(data[f])
            except Exception as e:
                return JSONResponse(
                    {"error": f"feature '{f}' must be numeric: {e}"}, status_code=400
                )

        df = pd.DataFrame([row])

        prediction = MODEL.predict(df)[0]

        result = {"prediction": float(prediction)}

        if hasattr(MODEL, "predict_proba"):
            proba = MODEL.predict_proba(df)[0].tolist()
            result["probabilities"] = proba

        PREDICTION_COUNT.inc()
        PREDICTION_LATENCY.observe(time.time() - start_time)

        return JSONResponse(result)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ------------------------------------------------------------
# PAGE HTML
# ------------------------------------------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>Prédiction de priorisation d'accident </title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        input { margin-bottom: 8px; width: 150px; }
        .row { display: flex; flex-wrap: wrap; gap: 10px; }
        .field { display: flex; flex-direction: column; }
        button { padding: 8px 15px; margin-top: 10px; }
    </style>
</head>
<body>
<h1>Prédiction d'accident</h1>

<div class="row">
"""

for feat, sample, label in zip(FEATURES, SAMPLE, FEATURE_LABELS):
    if feat in CHOICES and isinstance(CHOICES[feat], dict) and len(CHOICES[feat]) > 0:
        HTML += f'<div class="field"><label for="{feat}_select">{label}</label>\n'
        HTML += f'  <select id="{feat}_select" data-feature="{feat}">\n'
        for code, lib in sorted(
            CHOICES[feat].items(), key=lambda x: (x[0] is None, x[0])
        ):
            code_str = "" if code is None else str(code)
            selected = ""
            if float(sample) == float(code):
                selected = " selected"
            HTML += f'    <option value="{code_str}"{selected}>{lib}</option>\n'
        HTML += "  </select>\n"
        HTML += "</div>\n"

    else:
        # champ numérique classique
        value_attr = f' value="{sample}"' if sample is not None else ""
        HTML += (
            f'<div class="field">'
            f'<label for="{feat}">{label}</label>'
            f'<input id="{feat}" type="number" step="any"{value_attr}/>'
            f"</div>\n"
        )

HTML += """
</div>

<button onclick="predict()">Prédire</button>

<pre id="result"></pre>

<script>


const FIELDS = ["""

for feat in FEATURES:
    HTML += f'  "{feat}",'

HTML += (
    """];

function collectPayload() {
  const payload = {};
  for (const feat of FIELDS) {
    const sel = document.getElementById(`${feat}_select`);
    if (sel) {
      const v = sel.value;
      payload[feat] = (v === "" ? null : Number(v));
      continue;
    } const inp = document.getElementById(feat);
    if (inp) {
      const v = inp.value;
      payload[feat] = (v === "" ? null : Number(v));
    } else {
      payload[feat] = null;
    }
  }
  return payload;
}


async function predict() {
    let payload = collectPayload();
    const r = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    const txt = await r.text();
    const data = JSON.parse(txt);
    const pred = Number(data?.prediction);
    if (pred === 1 ) {
        header ="Accident prioritaire";
    } else {
        header = "Accident non prioritaire";
    }
    document.getElementById("result").innerText = header + txt;
}
</script>
</body>
</html>
"""
    % FEATURES
)


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML
