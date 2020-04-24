FROM python:3.7.7-slim-buster

RUN apt-get update \
    && apt-get upgrade -y \
    && pip3 install --upgrade pip
