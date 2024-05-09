FROM ubuntu:22.04

ADD /src/api/api.py /home/shield/src/api/ 
ADD /src/api/test_api.py /home/shield/src/api
ADD /src/data/update_data.py /home/shield/src/data/
ADD /src/data/make_dataset.py /home/shield/src/data/
ADD /src/models/train_model.py /home/shield/src/models/
ADD /src/api/requirements_api.txt /home/shield/src/api/
ADD src/models/test_features.json /home/shield/src/models/
# Copy Logs folder in its entirety: 
ADD logs /home/shield/logs

WORKDIR /home/shield/
VOLUME /home/volume/
EXPOSE 8006

RUN apt-get update \
&& apt-get install python3-pip -y\
&& pip3 install -r /home/shield/src/api/requirements_api.txt

CMD ["/bin/bash", "-c", "\
# Import users_db.json from volume:
mkdir src/users_db ; \
cp ../volume/src/users_db/users_db.json src/users_db ; \
# Import model save from volume:
mkdir models ; \
cp ../volume/models/trained_model.joblib models ; \
# Import data from volume:
cp -r ../volume/data data ; \
# Run the test:
python3 src/api/test_api.py \
"]