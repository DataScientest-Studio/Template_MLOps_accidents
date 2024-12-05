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
            login_db = container "Login Database" "User storage" "PostgreSQL" {
                tags "Database"
            }
            loginAPI.repository_jdbc -> login_db "read/write" "sql"
        }
        train_software_system = softwareSystem "Apprentissage du modèle de prédiction de la gravité des accidents de la route" {
            group steps {
                init = container "0. Run a new experiment with API" "API" "Python" {
                    tags "Python", "FastAPI"
                }
                extract = container "1. Extract data" "Extract data from external system and save it in repository" "Python" {
                    tags "Python"
                }
                transform = container "2. Transform data" "Transform data and save it in repository" "Python" {
                    tags "Python"
                }
                training = container "3. & 4. Model training / Repository" "Model training, save experiments, and manage deploiement workflow" "Python" {
                    tags "Python"
                    training_model = component "3. Training model" "Training model and push experiment to repository" "Python" {
                        tags "Python"
                    }
                    training_api = component "4. Deploiement workflow API" "API to manage deploiements and deploy model" "FastAPI" {
                        tags "Python", "FastAPI"
                    }
                    mlflow = component "Model Storage" "Store, vizualize mobel performance and manage deploiement deploiement" "MLFlow" {
                        tags "ExternalTool"
                    }
                    training_model -> mlflow "push" "experiment"
                    training_api -> mlflow "model selection" "http"
                    training_api -> mlflow "load" "sdk"
                }
            }
            lakefs = container "LakeFS" "Data repository" "LakeFS" {
                tags "ExternalTool"
            }

            streaming = container "Streaming" "Use it to sequence the model workflow" "Kafka" {
                tags "Streaming"
            }

            redis = container "Redis" "Manage deploiements and deploiement workflow" "Redis" {
                tags "Database"
            }

            init -> streaming "produce" "kafka"
            extract -> streaming "consume" "kafka"
            extract -> streaming "produce" "kafka"
            transform -> streaming "consume" "kafka"
            transform -> streaming "produce" "kafka"
            training.training_model -> streaming "consume" "kafka"

            extract -> lakefs "push data" "http"
            transform -> lakefs "read&push data/pull request" "http"
            training -> lakefs "read data" "http"
            training -> lakefs "merge" "http"
            training.training_model -> lakefs "read" "experiment"
            training.training_api -> redis "cache model" "http"
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
            adminAPI -> predict_db "read/write" "sql"

            predictAPI -> loginss.loginAPI "read" "http"
            predictAPI -> predict_db "read/write" "sql"
            predictAPI -> train_software_system.redis "copy model" "docker"
        }

        policier -> service_sofware_system.front "Uses" "Get prediction"
        admin -> service_sofware_system.front "Show historique/statistique"
        admin -> train_software_system.training.mlflow "Manage model" "web"
        admin -> train_software_system.training.training_api "Choose model version / Update model cache"
        admin -> train_software_system.init "write" "http"
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

        component train_software_system.training "training_Level_3" {
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
                background #555555
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
