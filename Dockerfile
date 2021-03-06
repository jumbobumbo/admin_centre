FROM python:3.8.2-slim-buster

# UPDATE/UPGRADE PACKAGES AND PIP
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install iputils-ping -y \
    && pip3 install --upgrade pip

# INSTALL REQUIREMENTS
COPY requirements.txt /
RUN pip3 install -r requirements.txt

# CREATE LOCAL/TATGET/APP DIRS & COPY APP INTO CONTAINER
RUN mkdir hostfs \
    && mkdir target \
    && mkdir app
COPY app /app
