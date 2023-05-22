FROM python:3-slim
RUN pip install --upgrade pip && pip install pika requests pandas
RUN pip install google-auth google-cloud-core google-cloud-vision Pillow
RUN pip install psycopg2-binary sqlalchemy
RUN pip install minio
#RUN echo 'alias j="jupyter lab --ip 0.0.0.0 --no-browser"' >> ~/.bashrc
#EXPOSE 8888
WORKDIR /srv