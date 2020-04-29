# Dockerfile for GEO database, for a development container

# Using debian 10 (buster) as base image
FROM debian:buster

# Set maintainer label
LABEL maintainer="André Moreira Souza <msouza.andre@hotmail.com>"

# Update packages
RUN apt-get update -y && apt-get upgrade -y

# Import repository signing key, and update package lists
RUN apt-get install -y apt-utils
RUN apt-get install -y wget curl ca-certificates gnupg
RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# Add PostgreSQL repository
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list

# Install postgresql-11
RUN apt-get install -y build-essential tar gzip bzip2 zlib1g readline-common postgresql-11 postgresql-client-11 libpq-dev

# Install python, pip and package requirements
RUN apt-get install -y python3 python3-dev python3-pip postgresql-plpython3-11
COPY ./requirements.txt /opt/app/requirements.txt
RUN pip3 install --upgrade --force-reinstall -r /opt/app/requirements.txt

# Download NLTK resources
RUN python3 -c "import nltk; dir='/usr/share/nltk_data' ;nltk.download('punkt', dir); nltk.download('stopwords', dir); nltk.download('rslp', dir); nltk.download('averaged_perceptron_tagger', dir); nltk.download('maxent_ne_chunker', dir); nltk.download('words', dir)"

# Run the rest of the commands as the ``postgres`` user created by the ``postgresql-11`` package when it was ``apt-get installed``
USER postgres

# Create "geo" database with the user "postgres" as owner
# Execute schema.sql script on "geo" database, creating all the structure
COPY ./schema.sql /opt/app/schema.sql
RUN /etc/init.d/postgresql start && createdb -O postgres geo && psql -d geo -f /opt/app/schema.sql

# # Adjust PostgreSQL configuration so that remote connections to the
# # database are possible.
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/11/main/pg_hba.conf

# # And add ``listen_addresses`` to ``/etc/postgresql/11/main/postgresql.conf``
RUN echo "listen_addresses='*'" >> /etc/postgresql/11/main/postgresql.conf

# Expose the PostgreSQL port
EXPOSE 5432

# Add VOLUMEs to allow backup of config, logs and databases
VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]

# Set the default command to run when starting the container
CMD ["/usr/lib/postgresql/11/bin/postgres", "-D", "/var/lib/postgresql/11/main", "-c", "config_file=/etc/postgresql/11/main/postgresql.conf"]
