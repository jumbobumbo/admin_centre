FROM python:3.7.7-slim-buster

# UPDATE/UPGRADE PACKAGES AND PIP
RUN apt-get update \
    && apt-get upgrade -y \
    && pip3 install --upgrade pip

# INSTALL REQUIREMENTS
COPY requirements.txt /
RUN pip3 install -r requirements.txt

# COPY APP INTO CONTAINER
RUN mkdir app
COPY app /app
