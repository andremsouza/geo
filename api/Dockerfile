# Dockerfile for GEO api

# Using debian 10 (buster) as base image
FROM debian:buster

# Set maintainer label
LABEL maintainer="André Moreira Souza <msouza.andre@hotmail.com>"

# Update packages, install python, install psycopg2 requirements
RUN apt-get update -y && apt-get upgrade -y && apt-get install -y python3 python3-dev python3-pip build-essential libpq-dev

# Install app requirements with pip
COPY ./requirements.txt /opt/app/requirements.txt
RUN pip3 install --upgrade --force-reinstall -r /opt/app/requirements.txt

# Copy local app files
COPY ./*.py /opt/app/
WORKDIR /opt/app/

# Expose the flask port
EXPOSE 5000

# Set the default command to run when starting the container
# ENTRYPOINT ["python3"]
CMD python3 /opt/app/api.py -H $HOSTNAME -p $PORT -d $DBNAME -u $USERNAME --password --min-connections $CONNMIN --max-connections $CONNMAX
