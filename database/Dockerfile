# Dockerfile for GEO database, for a development container

# Using debian 10 (buster) as base image
FROM debian:buster

# Import repository signing key, and update package lists
RUN apt-get update && apt-get install -y apt-utils
RUN apt-get update && apt-get install -y wget curl ca-certificates gnupg
RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# Add PostgreSQL repository
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ buster-pgdg main" > /etc/apt/sources.list.d/pgdg.list

# Install postgresql-11
RUN apt-get update && apt-get install -y build-essential tar gzip bzip2 zlib1g readline-common postgresql-11

# Install python, pip and package requirements
RUN apt-get update && apt-get install -y python3 python3-pip postgresql-plpython3-11
COPY ./requirements.txt /opt/app/requirements.txt
RUN pip3 install --upgrade --force-reinstall -r /opt/app/requirements.txt

# Run the rest of the commands as the ``postgres`` user created by the ``postgresql-11`` package when it was ``apt-get installed``
USER postgres

# Create a PostgreSQL role named ``docker`` with ``docker`` as the password and
# then create a database `docker` owned by the ``docker`` role.
# Note: here we use ``&&\`` to run commands one after the other - the ``\``
#       allows the RUN command to span multiple lines.
RUN /etc/init.d/postgresql start &&\
    psql --command "CREATE USER docker WITH SUPERUSER PASSWORD 'docker';" &&\
    createdb -O docker docker

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