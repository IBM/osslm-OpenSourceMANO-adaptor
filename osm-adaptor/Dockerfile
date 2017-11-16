FROM ansible/ansible:ubuntu1604py3

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apt-get update
RUN apt-get install libcurl4-gnutls-dev libgnutls-dev -y
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install git+https://osm.etsi.org/gerrit/osm/osmclient

COPY . /usr/src/app

EXPOSE 8081
CMD ["python3","-m", "swagger_server"]
