FROM alpine:latest

ADD /src/monitoring/monitoring.py /home/shield/src/monitoring/

WORKDIR /home/shield/

VOLUME /home/volume/
EXPOSE 8008

RUN apk update \
&& apk add python3 \
&& apk add py3-requests \
&& apk add curl

# CMD tail -f /dev/null 
CMD python3 src/monitoring/monitoring.py