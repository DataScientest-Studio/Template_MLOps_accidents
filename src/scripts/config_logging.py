import logging
import os

def setup_logging(log_file='app.log'):
    """
    Description:
    Configurer le logging .

    Args:
    - log_file (str): chemin vers le fichier où les logs seront écrits.

    Returns:
    - None
    """
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logging.basicConfig(
        level=logging.DEBUG,  # Niveau minimum de log à capturer
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Format des messages de log
        handlers=[
            logging.FileHandler(f'logs/{log_file}'),  # Fichier où les logs seront écrits
            logging.StreamHandler()  # Console où les logs seront affichés
        ]
    )
