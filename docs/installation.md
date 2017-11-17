# Installation
## Get the code
Download or clone the repository to your target host.

## Pre-Install Configuration
Adjust these settings to fit your needs.
NOTE: You **MUST** modify the **osm_host** setting to reflect your setup

File: _osslm-OpenSourceMANO-adaptor/alm-osm-rm-docker-compose.yml_

| property | default | comment|
|----------|---------|--------|
|networks.default.ipam.config.subnet|10.10.10.10/24|docker network, modify if clashes with existing subnet configs |
|services.alm-osm-rm.ports|8081|swagger API port|
|services.alm-osm-rm.environment.LOG_LEVEL|DEBUG|log level. Supported values: INFO, ERROR, WARNING, DEBUG|
|services.alm-osm-rm.environment.extra_hosts.kafka|192.168.63.179|IP address of your ALM kafka/zookeeper instance|

File: _osslm-OpenSourceMANO-adaptor/osm-adaptor/config.yml_
| property | default | comment|
|----------|---------|--------|
|driver.supportedFeatures.AsynchronousTransitionResponses|false| set to _true_ if you want to suppor async mode |
|osm.osm_host|192.168.65.49| the IP address of your OSM REST API endpoint |



## Run

```
cd into the osslm-OpenSourceMANO-adaptor  directory
docker-compose -f alm-osm-rm-docker-compose.yml build
docker-compose -f alm-osm-rm-docker-compose.yml up -d
```

You can modify the port the RM is listening in the docker-compose file (default is 8081).

## Access
you can access the swagger API using: http://yourserverip:8081/api/v1.0/resource-manager/ui/#/

## Post-install Configuration
1. launch the swagger API page and
2. expand the "Driver janitor" section

### Create the Database Schema
3. run the "Create database tables" operation

This creates the alm_osm keyspace and all required tables in the db.
