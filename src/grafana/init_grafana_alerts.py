import os
import sys
import time
import json
import requests
from typing import Optional, Dict, Any

# --- CONFIGURATION GÉNÉRALE ---
GRAFANA_URL = os.getenv("GRAFANA_URL")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Chemins des fichiers de configuration (montés via Docker)
CONTACT_POINT_FILE = "/config/contact-points.json"
POLICIES_FILE = "/config/notification-policies.json"

# Chemins vers vos fichiers de règles d'alerte
ALERT_RULES_FILES = [
    {"path": "/alert-rules/alert-error-rate.json", "name": "Taux d'erreur"},
    {"path": "/alert-rules/alert-latency.json", "name": "Latence P95"},
]

def load_json_config(file_path: str) -> Optional[Dict[str, Any]]:
    """Charge un fichier JSON et retourne son contenu sous forme de dictionnaire."""
    if not os.path.exists(file_path):
        print(f"❌ Fichier de configuration introuvable : {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Configuration chargée depuis : {file_path}")
        return data
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de syntaxe JSON dans {file_path} : {e}")
        return None
    except Exception as e:
        print(f"❌ Erreur lecture fichier {file_path} : {e}")
        return None

def wait_for_grafana(timeout: int = 60) -> bool:
    """Attend que l'API Grafana soit disponible."""
    print("🔍 Attente que Grafana soit disponible...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Grafana est en ligne !")
                return True
            elif response.status_code == 401:
                print("❌ Erreur d'authentification (401). Vérifiez vos identifiants (ID_GRAFANA/MP_GRAFANA).")
                return False
        except requests.exceptions.RequestException:
            pass 
        time.sleep(2)
    
    print("❌ Timeout : Grafana n'est pas disponible après {} secondes.".format(timeout))
    return False

def create_or_get_folder(session: requests.Session) -> Optional[str]:
    """Crée le dossier d'alertes ou récupère son UID s'il existe."""
    FOLDER_NAME = "MLOps_Alerts"
    FOLDER_UID = "mlops-alerts-folder"
    
    print(f"📁 Vérification/Création du dossier : {FOLDER_NAME}...")
    
    payload = {"uid": FOLDER_UID, "title": FOLDER_NAME}
    try:
        response = session.post(f"{GRAFANA_URL}/api/folders", json=payload)
        
        if response.status_code in [200, 201]:
            print(f"✅ Dossier créé avec UID: {FOLDER_UID}")
            return FOLDER_UID
        elif response.status_code == 409:
            print(f"ℹ️  Dossier déjà existant (Conflit 409 - UID: {FOLDER_UID}).")
            return FOLDER_UID
        elif response.status_code == 412:
            # 412 signifie souvent "Precondition Failed" mais peut arriver si le titre existe déjà avec un UID différent
            # ou si le dossier existe déjà. On tente de le récupérer.
            print(f"ℹ️  Dossier semble exister (Erreur 412). Tentative de récupération...")
            # On peut essayer de lister les dossiers pour trouver celui avec le bon UID ou Titre
            resp_list = session.get(f"{GRAFANA_URL}/api/folders")
            if resp_list.status_code == 200:
                folders = resp_list.json()
                for f in folders:
                    if f.get('uid') == FOLDER_UID or f.get('title') == FOLDER_NAME:
                        print(f"✅ Dossier retrouvé : {f.get('title')} (UID: {f.get('uid')})")
                        return f.get('uid')
            print(f"⚠️  Impossible de retrouver le dossier existant.")
            return None
        else:
            print(f"⚠️  Erreur création dossier (Code: {response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception lors de la création du dossier: {e}")
        return None

def configure_contact_point(session: requests.Session) -> bool:
    """Configure le point de contact depuis le fichier JSON."""
    
    config = load_json_config(CONTACT_POINT_FILE)
    if not config:
        return False

    if not DISCORD_WEBHOOK_URL:
        print("❌ ERREUR CRITIQUE : Variable d'environnement DISCORD_WEBHOOK_URL manquante.")
        return False

    # 1. Définir le nom DU DÉBUT pour qu'il soit accessible partout dans la fonction
    contact_name = config.get('name', 'Inconnu')

    # Injection sécurisée de l'URL du webhook
    if "settings" in config and "url" in config["settings"]:
        config["settings"]["url"] = DISCORD_WEBHOOK_URL
        print("🔒 URL du Webhook injectée dynamiquement depuis les variables d'environnement.")

    print(f"📞 Vérification/Configuration du Contact Point : {contact_name}...")

    # 2. Vérifier si le contact point existe déjà par son nom
    try:
        response_list = session.get(f"{GRAFANA_URL}/api/v1/provisioning/contact-points")
        if response_list.status_code == 200:
            existing_contacts = response_list.json()
            # Chercher un contact avec le même nom
            for contact in existing_contacts:
                if contact.get('name') == contact_name:
                    print(f"ℹ️  Contact Point '{contact_name}' déjà existant (UID: {contact.get('uid')}).")
                    return True
    except Exception as e:
        print(f"⚠️  Impossible de lister les contacts existants : {e}")
        # On continue quand même pour tenter la création

    # 3. S'il n'existe pas, on le crée
    # La variable contact_name est déjà définie plus haut, donc pas de NameError ici
    print(f"   → Création du nouveau Contact Point '{contact_name}'...")
    
    try:
        response = session.post(f"{GRAFANA_URL}/api/v1/provisioning/contact-points", json=config)
        
        if response.status_code in [200, 201, 202]:
            print("✅ Contact Point créé avec succès !")
            return True
        elif response.status_code == 401:
            print("❌ Erreur d'authentification (401) lors de la création du Contact Point.")
            return False
        elif response.status_code == 409:
            print("ℹ️  Contact Point déjà existant (conflit 409).")
            return True
        else:
            print(f"❌ Erreur création Contact Point (Code: {response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception configuration Contact Point: {e}")
        return False

def inject_alert_rule(session: requests.Session, file_path: str, rule_name: str) -> bool:
    """Injecte une règle d'alerte depuis un fichier JSON."""
    if not os.path.exists(file_path):
        print(f"⚠️  Fichier de règle introuvable : {file_path}")
        return False

    print(f"   🚨 Injection de la règle : {rule_name}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            payload = f.read()
        
        response = session.post(
            f"{GRAFANA_URL}/api/v1/provisioning/alert-rules",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            print(f"   ✅ Règle [{rule_name}] injectée.")
            return True
        elif response.status_code == 401:
            print(f"   ❌ Erreur d'authentification (401) pour la règle [{rule_name}].")
            return False
        elif response.status_code == 409:
            print(f"   ℹ️  Règle [{rule_name}] existe déjà.")
            return True
        else:
            print(f"   ❌ Erreur Règle [{rule_name}] (Code: {response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception injection règle [{rule_name}]: {e}")
        return False

def configure_notification_policies(session: requests.Session) -> bool:
    """Configure les politiques de notification depuis le fichier JSON."""
    
    config = load_json_config(POLICIES_FILE)
    if not config:
        return False

    print("📢 Configuration des Notification Policies...")
    
    try:
        response = session.put(f"{GRAFANA_URL}/api/v1/provisioning/policies", json=config)
        
        if response.status_code in [200, 202]:
            print("✅ Policies configurées.")
            return True
        elif response.status_code == 401:
            print("❌ Erreur d'authentification (401) lors de la configuration des Policies.")
            return False
        else:
            print(f"❌ Erreur Policies (Code: {response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception configuration Policies: {e}")
        return False

def main():
    # 1. Vérification de la connexion et de l'authentification
    if not wait_for_grafana():
        sys.exit(1)

    session = requests.Session()

    # 2. Création du dossier
    folder_uid = create_or_get_folder(session)
    if not folder_uid:
        print("⚠️  Impossible de créer le dossier. Vérifiez les logs ci-dessus.")
        # On ne sort pas forcément ici, car les règles JSON pourraient avoir un folderUID en dur

    # 3. Contact Point
    if not configure_contact_point(session):
        print("❌ Échec configuration Contact Point. Arrêt.")
        sys.exit(1)
    
    time.sleep(2)

    # 4. Notification Policies
    if not configure_notification_policies(session):
        print("⚠️  Échec configuration Policies, mais on continue...")

    # 5. Règles d'alerte
    print(f"🚨 Injection des règles d'alerte...")
    success_count = 0
    for rule_info in ALERT_RULES_FILES:
        if inject_alert_rule(session, rule_info["path"], rule_info["name"]):
            success_count += 1
    
    print(f"✅ Initialisation terminée. {success_count}/{len(ALERT_RULES_FILES)} règles traitées avec succès.")

if __name__ == "__main__":
    main()