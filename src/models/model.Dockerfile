FROM ubuntu:22.04

ADD /src/models/train_model.py /home/shield/src/models/

WORKDIR /home/shield/

EXPOSE 8004

RUN apt-get update \
&& apt-get install python3-pip -y\
&& pip install numpy \
&& pip install pandas \
&& pip install joblib \
&& pip install scikit-learn

CMD ["/bin/bash", "-c", "\
# Import train data (previously created in step 2) from volume to container:
cp -r ../volume/data data ; \
# Make requested directory:
mkdir models ; \
# Train model:
python3 src/models/train_model.py ; \
# Create directory inside volume for model save:
mkdir ../volume/models ; \
# Copy model save into volume for persistency:
cp models/trained_model.joblib  ../volume/models/ \
"]


# TO KEEP:
# Here is the previous version of this dockerfile which used alpine as os for a lighter image.
# Compatibility issues arised for model save between this container and the api one (build from ubuntu:22.04), 
# due to different versions of libraries used (sklearn).
# In order to quickly have a full docker-compose working, I decided to build this image according to the api one.
# It might be interresting to keep the code below to do the opposite: build this image accordingdly, 
# and try to lighten the api image (which currently weights nearly 1Go) by building it from alpine too.
# 
#FROM alpine:latest
#
#ADD /src/models/train_model.py /home/shield/src/models/
#
#WORKDIR /home/shield/
#
#EXPOSE 8004
#
#RUN apk update \
#&& apk add python3 \
#&& apk add py3-numpy \
#&& apk add py3-pandas \
#&& apk add py3-joblib \
#&& apk add py3-scikit-learn
#
#CMD ["/bin/sh", "-c", "cp -r ../volume/data data ; python3 src/models/train_model.py ; mkdir ../volume/models ; cp src/models/trained_model.joblib  ../volume/models/"]