FROM postgres:13

# Définir les variables d'environnement pour PostgreSQL
ENV POSTGRES_DB=accidents
ENV POSTGRES_USER=my_user
ENV POSTGRES_PASSWORD=your_password

# Copier le fichier CSV et le script SQL dans le répertoire d'initialisation de PostgreSQL
COPY ./data_2005a2021_final.csv /docker-entrypoint-initdb.d/data_2005a2021_final.csv
COPY ./init.sql /docker-entrypoint-initdb.d/init.sql
# Récupérer et afficher les résultats
