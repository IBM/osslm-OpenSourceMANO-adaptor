"""
deployment location controller
- list locations
- get location by name
- list locations with properties

IBM Corporation, 2017, jochen kappel
"""
import connexion
from swagger_server.models.inline_response20010 import InlineResponse20010
from swagger_server.models.inline_response20012 import InlineResponse20012
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime

# business logic imports
from flask import abort
from flask import current_app as app
from .driver_config import ConfigReader
from .asm_osmclient import OsmClient
from .cassandra import CassandraHandler
import uuid
import json

def topology_deployment_locations_get():
    """
    get list of deployment locations
    Returns a list of all deployment locations available
    to this Resource Manager

    :rtype: List[InlineResponse20010]
    """
    osmVim = OsmClient().getVim()

    osmVimList = osmVim.list(False)
    # get list of OSM data centers
    app.logger.debug("vims found " + str(osmVimList))
    almLocs = []
    for vim in osmVimList:
        app.logger.debug("DC found: " + str(vim))
        # select only name and type
        almLocs.append(InlineResponse20010(vim["name"], vim["type"]))
    app.logger.debug("building deployment locations list" + str(almLocs))

    return almLocs


def topology_deployment_locations_name_get(name):
    """
    get details of a deployment location
    Returns information for the specified deployment location
    :param name: Unique name for the location requested
    :type name: str

    :rtype: InlineResponse20010
    """
    osmVim = OsmClient().getVim()

    vim = osmVim.get_datacenter(name)

    if vim is not None:
        app.logger.info("DC found: " + str(vim))
        # vim only contains name and uuid, need to get through list to get more
        app.logger.debug("datacenter found: " + str(vim))

        vimList = osmVim.list(False)
        for aVim in vimList:
            if aVim["name"] == vim["name"]:
                app.logger.info("got details for " + aVim["name"])
                return InlineResponse20010(aVim["name"], aVim["type"])
        app.logger.error("This should not happen. " + vim["name"] + " found but not in list " + str(vimList))
    else:
        app.logger.warning('no location found for ' + name)
        abort (404, 'no location found for ' + name)



def topology_deployment_locations_name_instances_get(name,
                                                     instanceType=None,
                                                     instanceName=None):
    """
    search for resource instances of a deployment location
    Searches for resource instances managed within the specified deployment
    location. The search can be restricted by the type of the resources to be
    returned, or a partial match on the name of the resources.
    :param name: Unique name for the deployment location
    :type name: str
    :param instanceType: Limits results to be of this resource type
    (optional, exact matches only)
    :type instanceType: str
    :param instanceName: Limits results to contain this string in the name
    (optional, partial matching)
    :type instanceName: str

    :rtype: List[InlineResponse20012]
    """
    return 'do some magic!'


def topology_instances_id_get(id):
    """
    get details for a resource instance
    Returns information for the specified resource instance
    :param id: Unique id for the resource instance
    :type id: str

    :rtype: InlineResponse20012
    """
    app.logger.info('getting details for instance: ' + id)

    try:
        val = uuid.UUID(id)
    except ValueError:
        app.logger.error('id ' + id + ' is not a valid UUID' )
        abort (400, 'not a valid UUID')

    rcode, payload = get_instance( id )
    app.logger.debug('instance ' + id + 'details: ' + str(payload))

    if rcode == 200:
        return payload
    else:
        abort( 404,'')

def get_instance(instanceId):
    """
    get properties of one instance
    """
    dbsession = CassandraHandler().get_session()
    app.logger.info('searching for instance id: ' + instanceId)

    query = """SELECT resourceId as "resourceId",
        resourcename as "resourceName",
        resourcetype as "resourceType",
        resourcemanagerid as "resourceManaerId",
        deploymentlocation as "deploymentLocation",
        createdat as "createdAt",
        lastmodifiedat as "lastModifiedAt",
        properties as "properties",
        toJson(internalResourceInstances) as "internalResourceInstances"
        FROM instances WHERE resourceId = %s"""
    rows = dbsession.execute(query, [uuid.UUID(instanceId)])

    if rows:
        for row in rows:
            if row['properties'] is None:
                row['properties'] = {}
            else:
                row['properties'] = dict(row['properties'])

            row['internalResourceInstances'] = json.loads(row['internalResourceInstances'])
            row['resourceId'] = str(row['resourceId'])
            row['createdAt'] = row['createdAt'].strftime('%Y-%m-%dT%H:%M:%SZ')
            row['lastModifiedAt'] = row['lastModifiedAt'].strftime('%Y-%m-%dT%H:%M:%SZ')
            app.logger.info('resource instance found')
        app.logger.debug(str(row))
        return 200, row
    else:
        app.logger.info('no instance found for id: ' + instanceId)
        return 404, ''
