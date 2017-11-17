# Installation
Download or clone the repository to your target host.

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
