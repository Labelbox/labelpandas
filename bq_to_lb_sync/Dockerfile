# Copyright 2021 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START eventarc_gcs_dockerfile]

# Use the official Python image.
# https://hub.docker.com/_/python
#FROM python:3.9
FROM python:3.9-slim-buster

RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0

    

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY *.* /app/

# Install production dependencies.
RUN pip install -r requirements.txt
#RUN pip install Flask==2.2.2 gunicorn>=20.0.4 requests==2.28.1 ptvsd==4.3.2 google-cloud-bigquery labelbase labelpandas>=0.1.34 google google-auth db-dtypes 
#ENTRYPOINT ["python", "main.py"]

# Run the web service on container startup. 
# Use gunicorn webserver with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
# [END eventarc_gcs_dockerfile]
