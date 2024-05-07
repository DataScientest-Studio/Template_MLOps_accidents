FROM alpine:latest

ADD /src/users_db/create_users_db.py /home/shield/src/users_db/

WORKDIR /home/shield/

EXPOSE 8003

RUN apk update \
&& apk add python3

CMD ["/bin/sh", "-c", "\
# Run script:
python3 src/users_db/create_users_db.py ; \
# Make requested directory on volume:
mkdir -p ../volume/src/users_db ; \
# Copy users_db.json to volume for persistency:
cp src/users_db/users_db.json ../volume/src/users_db/ \
"]

