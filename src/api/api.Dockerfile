FROM ubuntu:22.04

ADD /src/api/api.py /home/shield/src/api/ 
ADD /src/data/update_data.py /home/shield/src/data/
ADD /src/data/make_dataset.py /home/shield/src/data/
ADD /src/data/data_id.json /home/shield/src/data/
ADD /src/models/train_model.py /home/shield/src/models/
ADD /src/api/requirements_api.txt /home/shield/src/api/
ADD logs /home/shield/logs


WORKDIR /home/shield/
VOLUME /home/volume/
EXPOSE 8000

RUN apt-get update \
&& apt-get install python3-pip -y\
&& pip3 install -r /home/shield/src/api/requirements_api.txt  

CMD ["/bin/bash", "-c", "\
# Import users_db.json from volume:
mkdir src/users_db ; \
cp ../volume/src/users_db/users_db.json src/users_db ; \
# Import model save from volume:
mkdir models ; \
cp ../volume/models/rdf_v1.0_shield.joblib models ; \
# Import data from volume:
cp -r ../volume/data data ; \
# Export api script into volume:
mkdir -p ../volume/src/api ; \
cp src/api/api.py ../volume/src/api ; \
# Run the api:
uvicorn --app-dir src/api api:api --reload --host=0.0.0.0\
# TODO: Copy files modified by the api into volume:
"]


# --host=0.0.0.0 needed instead of --host=127.0.0.1
# More info here:
# https://stackoverflow.com/questions/1924434/what-is-the-curl-error-52-empty-reply-from-server
# --port=8000 : not needed in the call of uvicorn.

