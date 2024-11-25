workspace "Name" "Description" {

    !identifiers hierarchical

    # FastAPI yes
    # Docker yes
    # TU yes
    # MLflow yes - versionning des modeles - W&B no équivalent
    # Airflow Oui - nettoyage des données - ETL
    # DVC DagsHub - OK => pipeline entrainement
    # Grafana prometheus OK

    # Kubeflow ou ZenML => entrainement model
    # BentoML Non - package model avec API - Utilisation d'MLflow
    # Drift Monitoring NON - deja convert Graphana
    model {
        policier = person "Policier"
        admin = person "Admin"
        loginss = softwareSystem "Login system" {
            loginAPI = container "Login API" {
                main = component "Runner" {
                    tags "Python"
                }
                api = component "API" "FastAPI" {
                    tags "Python", "FastAPI"
                }
                domain = component "Domain" "Python" {
                    tags "Python", "domain"
                }
                repository_jdbc = component "JDBC repository" "sqlalchemy" {
                    tags "Python", "sqlalchemy"
                }
                repository_jwt = component "JWT repository" "authlib" {
                    tags "Python"
                }
                main -> api "uses" "Python"
                api -> domain "calls" "Python"
                repository_jdbc -> domain "implements" "sqlalchemy"
                repository_jwt -> domain "implements" "authlib"
            }
            login_db = container "Login Database" {
                tags "Database"
            }
            loginAPI.repository_jdbc -> login_db "read/write" "sql"
        }
        train_software_system = softwareSystem "Apprentissage du modèle de prédiction de la gravité des accidents de la route" {
            mlflow = container "Model Storage" "Store and vizualize mobel performance" "MLflow" {
                tags "ExternalTool"
            }
            airflow = container "ETL" "Extract, transform and load data" "Airflow" {
                tags "ExternalTool"
            }
            dvc = container "Trainning" "Train pipeline" "DVC"

            object_db = container "Object Database" "Store clean data" "MongoDB" {
                tags "Database"
            }

            streaming = container "Streaming" "Store new clean data to train" "Kafka" {
                tags "Streaming"
            }

            airflow -> object_db "write" "sql"

            dvc -> streaming "consume" "sql"
            dvc -> mlflow "push model" "http"

            mlflow -> loginss.loginAPI "log in"
            airflow -> loginss.loginAPI "log in"

            object_db -> streaming
        }
        service_sofware_system = softwareSystem "Service de prédiction de la gravité des accidents de la route" {
            front = container "Web Application" "Use of the prediction model" "Vue"
            bff = container "Back for frontend" "Creates separate backend services to be consumed by frontend applications" "Python"
            predictAPI = container "Prediction API (retrieve scoring, historique, update model, MLflow)" -> TODO
            adminAPI = container "Admin API"
            predict_db = container "Prediction Database" {
                tags "Database"
            }
            front -> bff "Uses"

            bff -> loginss.loginAPI "read/write" "http"
            bff -> predictAPI "read/write" "http"
            bff -> adminAPI "read/write" "http"

            adminAPI -> loginss.loginAPI "read/write" "http"
            adminAPI -> train_software_system.mlflow "read" "http"
            adminAPI -> predict_db "read/write" "sql"

            predictAPI -> loginss.loginAPI "read" "http"
            predictAPI -> predict_db "read/write" "sql"
            predictAPI -> train_software_system.mlflow "copy model" "docker"
        }

        policier -> service_sofware_system.front "Uses" "Get prediction"
        admin -> service_sofware_system.front "Show historique/statistique"
        admin -> train_software_system.mlflow "Manage model"
        admin -> train_software_system.airflow "Manage ETL"
    }

    views {
        systemContext service_sofware_system "Level_1" {
            include *
            autolayout lr
        }

        container service_sofware_system "service_sofware_system_Level_2" {
            include *
            autolayout lr
        }

        container train_software_system "train_software_system_Level_2" {
            include *
            autolayout lr
        }

        component loginss.loginAPI "login_Level_3" {
            include *
            autolayout lr
        }

        styles {
            element "Element" {
                color #ffffff
            }
            element "Person" {
                background #0000ff
                shape person
            }
            element "Software System" {
                background #f86628
            }
            element "Container" {
                background #f88728
            }
            element "Database" {
                shape cylinder
                background #10136b
}
            element "ExternalTool" {
                shape diamond
                background #ff0000
            }
            element "Streaming" {
                shape pipe
                background #ff008f
            }
            element "domain" {
                shape hexagon
                background #ff008f
            }
            element "Python" {
                shape pipe
                background #ff008f
            }
        }
    }

    configuration {
        #scope softwaresystem
    }

}