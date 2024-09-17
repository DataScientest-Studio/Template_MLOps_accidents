import psycopg2

# Connexion à la base de données
conn = psycopg2.connect(
    dbname="accidents",
    user="my_user",
    password="your_password",
    host="localhost",  # ou l'adresse IP de ton conteneur
    port="5432"
)

# Créer un curseur
cur = conn.cursor()

# Exécuter une requête SQL
cur.execute("SELECT * FROM donnees_accidents;")

# Récupérer et afficher les résultats
rows = cur.fetchall()
for row in rows:
    print(row)

# Fermer la connexion
cur.close()
conn.close()
