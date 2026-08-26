from datetime import datetime
import os
import json
import numpy as np
import pandas as pd
from scipy import stats

from airflow import DAG
from airflow.operators.python import PythonOperator

DATA_DIR = "/opt/airflow/data/preprocessed"
REFERENCE_PATH = os.path.join(DATA_DIR, "X_train.csv")
CURRENT_PATH = os.path.join(DATA_DIR, "X_test.csv")

# KS p-value threshold: below this = drift detected
P_VALUE_THRESHOLD = 0.05
# PSI threshold: above this = significant drift
PSI_THRESHOLD = 0.2


def _psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    ref_counts, bin_edges = np.histogram(reference, bins=bins)
    cur_counts, _ = np.histogram(current, bins=bin_edges)
    ref_pct = (ref_counts + 1e-8) / len(reference)
    cur_pct = (cur_counts + 1e-8) / len(current)
    return float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))


def compute_drift(**context):
    ref = pd.read_csv(REFERENCE_PATH)
    cur = pd.read_csv(CURRENT_PATH)

    numeric_cols = ref.select_dtypes(include=[np.number]).columns.tolist()

    results = {}
    drifted = []

    for col in numeric_cols:
        ref_vals = ref[col].dropna().values
        cur_vals = cur[col].dropna().values

        ks_stat, p_value = stats.ks_2samp(ref_vals, cur_vals)
        psi = _psi(ref_vals, cur_vals)

        has_drift = (p_value < P_VALUE_THRESHOLD) or (psi > PSI_THRESHOLD)

        results[col] = {
            "ks_stat": round(float(ks_stat), 4),
            "p_value": round(float(p_value), 4),
            "psi": round(psi, 4),
            "drift_detected": has_drift,
        }

        if has_drift:
            drifted.append(col)

    context["ti"].xcom_push(key="drift_results", value=results)
    context["ti"].xcom_push(key="drifted_columns", value=drifted)

    print(f"\n{'='*60}")
    print(f"Drift report — {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Reference : {REFERENCE_PATH} ({len(ref)} rows)")
    print(f"Current   : {CURRENT_PATH} ({len(cur)} rows)")
    print(f"{'='*60}")
    for col, r in results.items():
        flag = "DRIFT" if r["drift_detected"] else "OK"
        print(
            f"[{flag:5s}] {col:<25} KS={r['ks_stat']:.4f}  p={r['p_value']:.4f}  PSI={r['psi']:.4f}"
        )
    print(f"{'='*60}")
    print(f"Drifted columns ({len(drifted)}/{len(numeric_cols)}): {drifted}")


def alert_on_drift(**context):
    drifted = context["ti"].xcom_pull(key="drifted_columns", task_ids="compute_drift")
    results = context["ti"].xcom_pull(key="drift_results", task_ids="compute_drift")
    total = len(results)

    drift_ratio = len(drifted) / total if total else 0

    if drift_ratio >= 0.3:
        raise RuntimeError(
            f"ALERTE DRIFT : {len(drifted)}/{total} features en drift "
            f"({drift_ratio:.0%}). Ré-entraînement recommandé.\nFeatures: {drifted}"
        )

    if drifted:
        print(
            f"AVERTISSEMENT : {len(drifted)}/{total} features en drift "
            f"({drift_ratio:.0%}) — sous le seuil d'alerte (30%).\nFeatures: {drifted}"
        )
    else:
        print(f"Aucun drift détecté sur {total} features.")


default_args = {
    "owner": "mlops_team",
    "start_date": datetime(2026, 1, 1),
    "retries": 0,
}

with DAG(
    "drift_monitoring",
    default_args=default_args,
    description="Détecte le data drift entre référence (X_train) et données courantes (X_test)",
    schedule="@weekly",
    catchup=False,
    tags=["accidents", "drift"],
) as dag:

    task_compute = PythonOperator(
        task_id="compute_drift",
        python_callable=compute_drift,
    )

    task_alert = PythonOperator(
        task_id="alert_on_drift",
        python_callable=alert_on_drift,
    )

    task_compute >> task_alert
