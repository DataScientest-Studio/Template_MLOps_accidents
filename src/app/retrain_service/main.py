from fastapi import FastAPI, HTTPException

import subprocess

# Définir l'application FastAPI
app = FastAPI()


#définir un endpoint pour lancer un ré-entrainement
@app.post("/retrain")
def retrain():
    try:
        subprocess.run(["python", "train.py"], check=True)
        return {"message": "Re-entrainement réussi"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du re-entrainement: {e}")

