FROM alpine:latest

ADD /src/test/test_shield.py /home/shield/src/test/
ADD /src/models/test_features.json home/shield/src/models/

WORKDIR /home/shield/
VOLUME /home/volume/
EXPOSE 8007

RUN apk update \
&& apk add python3 \
&& apk add py3-requests \
&& apk add py3-pytest \
&& apk add curl

# CMD tail -f /dev/null 
CMD pytest src/test/test_shield.py