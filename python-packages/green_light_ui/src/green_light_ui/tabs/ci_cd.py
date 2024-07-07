import streamlit as st
import pandas as pd
import numpy as np

title = "CI/CD using GitHub and GitHub Actions"
sidebar_name = "CI/CD"


def run():

    st.title(title)

    st.markdown(
        """
        <style>
        .streamlit-expanderHeader p {
            font-size: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(
        "**Introduction**"
    ):
        st.write(
            """
    Since our project is a docker compose application that runs locally, in order to be able to use a form of Continuous Integration and Continuous Delivery (CI/CD) we decided to take advantage of Docker Hub and [Github Actions](https://docs.github.com/en/actions). 

    More specifically we created a Docker Hub repository named [`roadaccidentsmlops24`](https://hub.docker.com/u/roadaccidentsmlops24) and we used Github Actions to build and push our application's Docker images.
    
    There are 3 Dockerfiles:  

    * [`roadaccidentsmlops24/airflowdb`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/python-packages/airflowdb.Dockerfile) which is used as the base image of [Airflow running in docker compose](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html).
    * [`roadaccidentsmlops24/model_api`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/python-packages/model_api/Dockerfile) which is used for serving a trained ML model and user authorization purposes.
    * [`roadaccidentsmlops24/accidents_ui`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/python-packages/green_light_ui/Dockerfile) which is used to provide a UI for our project.
    """)

    with st.expander(
        "**The Continuous Integration Pipeline**"
    ):
        st.write(
            """
    The [Continuous Integration](https://github.com/DataScientest-Studio/may24_bmlops_accidents/actions/workflows/python-app.yml) (CI) pipeline for this project was developed using [Github Actions](https://docs.github.com/en/actions).
    
    More specifically:  

    * Every time a developer wants to merge their development branch to `Master` they start a new Pull Request (PR).
    * Then the [`python-app.yml`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.github/workflows/python-app.yml) workflow is executed, which for each of the [Python packages](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/python-packages) of this project will run the following steps:
        1. Checkout the repository.
        2. Install the Python package.
        3. Run the `pytest` tests of the Python package (typically found under a `tests/` directory).
        4. Build the `Dockerfile` successfully.
    * Every time the developer pushes new code to a PR branch, the CI pipeline starts again.""")



    with st.expander(
        "**The Continuous Delivery Pipeline**"
    ):
        st.write(
            """
    The [Continuous Delivery](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.github/workflows/build-and-push-docker-images.yml) (CD) pipeline for this project was developed using [Github Actions](https://docs.github.com/en/actions).
    
    More specifically:  

    * Every time a PR is merged to `Master` the CD pipeline runs ([example](https://github.com/DataScientest-Studio/may24_bmlops_accidents/actions/runs/9808426042)).
    * Then the [`build-and-push-docker-images.yml`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.github/workflows/build-and-push-docker-images.yml) workflow is executed, which for each of the [Python packages](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/python-packages) of this project will run the following steps:
        1. Checkout the repository.
        2. Login to Docker Hub using a Github [Secret](https://github.com/DataScientest-Studio/may24_bmlops_accidents/settings/secrets/actions) to store the password.
        3. Build the `Dockerfile` using two `tags` for each image: 
            * `latest`
            * Github action run number ([example](https://hub.docker.com/r/roadaccidentsmlops24/model_api/tags))
        4. Push the Docker built image to the [`roadaccidentsmlops24` Docker Repo](https://hub.docker.com/u/roadaccidentsmlops24).""")



    with st.expander("**The Release Pipeline**"):
        st.write(
            """
    Releasing the application using specific versions makes it possible to roll-back to a working version if/when something breaks.

    To enable versioned releases we use git's `tag` feature, more specifically:  

    * Every time a developer wants to create a new release of the application from the `master` branch, they would have to take the following steps:
        * `git checkout master`
        * `git pull origin master`
        * `git tag v{x}.{y}.{z}`, where the `v{x}.{y}.{z}` defines the [Semantic Versioning](https://semver.org/) of the release (eg: `v0.1.0`).
        * `git push origin --tags`
    * Then the [`deploy-docker-images-on-new-tag.yml`](https://github.com/DataScientest-Studio/may24_bmlops_accidents/blob/master/.github/workflows/deploy-docker-images-on-new-tag.yml) workflow is triggered, which for each of the [Python packages](https://github.com/DataScientest-Studio/may24_bmlops_accidents/tree/master/python-packages) of this project will run the following steps:
        1. Checkout the repository.
        2. Login to Docker Hub using a Github [Secret](https://github.com/DataScientest-Studio/may24_bmlops_accidents/settings/secrets/actions) to store the password.
        3. Build the `Dockerfile` successfully using two `tags` for each image: 
            * `latest`
            * The specified tag version ([example `roadaccidentsmlops24/model_api:v0.0.4`](https://hub.docker.com/layers/roadaccidentsmlops24/model_api/v0.0.4/images/sha256-7aecabc78a37a5318910f6d892b386aefb52bfbd6b39f3af8294f897a2ed9535?context=explore))
        4. Push the Docker built image to the [`roadaccidentsmlops24` Docker Repo](https://hub.docker.com/u/roadaccidentsmlops24).

    ---
   
    > A specific release (`tag`) version can be used when starting the Docker Compose app in `production` mode, by setting the environment variable `GLS_TAG` (`GLS` is an abbrv. of Green Light Services):

        * GLS_TAG="v0.0.4" DOCKER_BUILDKIT=1 docker compose up -d # OR
        * GLS_TAG="v0.0.4" ./PROD-docker-compose-up.sh

    > If the `GLS_TAG` environment variable is not set, then the `latest` tag will be used.
    
    > When running the application in the `development` mode using the `DEV-docker-compose-up.sh`, the environment variable `GLS_TAG` has no effect. In `development` mode, the Docker images are build using the local `Dockerfiles` instead of being pulled from the Docker Hub.""")

    with st.expander("**Improvements**"):

        st.write("TODO")
