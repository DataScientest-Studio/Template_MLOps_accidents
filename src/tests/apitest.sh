#!/bin/bash

# Basisdaten (können gleich bleiben)
URL="http://localhost:3000/predict"
AUTH_HEADER="Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX2lkXzEyMyIsImV4cCI6MTc1MTIxMTk3NH0.4rUIFKSAnfJzMsIZ8ek1joqEuAXrmkgKIUyB7EFgHeM"

# Schleife 30x
for i in {1..150}; do
  # Beispielhafte Variation der Parameter
  victim_age=$((30 + i))
  hour=$((i % 24))
  jour=$((i % 7 + 1))
  lat=$(awk "BEGIN { printf \"%.4f\", 45.0 + (RANDOM % 1000) / 10000 }")
  long=$(awk "BEGIN { printf \"%.4f\", 5.0 + (RANDOM % 1000) / 10000 }")
  col=$(rand 1 6)
  

  # JSON-Daten vorbereiten
  read -r -d '' DATA <<EOF
{
  "place": 13,
  "catu": 1,
  "sexe": 2,
  "secu1": 1.0,
  "year_acc": 2023,
  "victim_age": $victim_age,
  "catv": 2,
  "obsm": 2,
  "motor": 2,
  "catr": 1,
  "circ": 2,
  "surf": 2,
  "situ": 2,
  "vma": 90,
  "jour": $jour,
  "mois": 2,
  "lum": 1,
  "dep": 38,
  "com": 38001,
  "agg_": 1,
  "int": 2,
  "atm": 1,
  "col": 2,
  "lat": $lat,
  "long": $long,
  "hour": $hour,
  "nb_victim": 1,
  "nb_vehicules": 2
}
EOF

  echo "Sende Anfrage #$i mit hour=$hour, victim_age=$victim_age, jour=$jour"

  # Curl-Befehl
  curl -s -X POST "$URL" \
    -H "accept: application/json" \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d "$DATA"

  echo -e "\n----------------------------------------"
done
