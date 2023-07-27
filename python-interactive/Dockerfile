FROM python:3-slim
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 zbar-tools  -y
RUN pip install --upgrade pip && pip install pika requests pandas numpy
RUN pip install google-auth google-cloud-core google-cloud-vision Pillow
RUN pip install psycopg2-binary sqlalchemy
RUN pip install minio pyzbar opencv-python scikit-image
#RUN echo 'alias j="jupyter lab --ip 0.0.0.0 --no-browser"' >> ~/.bashrc
#EXPOSE 8888
WORKDIR /srv