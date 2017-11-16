"""
type controller
- list types
- get type by name

IBM Corporation, 2017, jochen kappel
"""
import connexion
from swagger_server.models.inline_response2008 import InlineResponse2008
from swagger_server.models.inline_response2009 import InlineResponse2009
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime

# business logic imports
from flask import abort
from flask import current_app as app
import yaml
from .driver_config import ConfigReader
from .asm_osmclient import OsmClient


def types_get():
    """
    Get list of supported resource types
    Returns a list of all resource types managed by this Resource Manage

    :rtype: List[InlineResponse2008]
    """
    osmNsd = OsmClient().getNsd()

    # get all OSM network service descriptors (NSD)
    osmNsdList = osmNsd.list()

    almTypes = []
    for nsd in osmNsdList:
        app.logger.debug('got NSD ' + str(nsd))
        # select name and version from NSD dict
        almTypes.append(InlineResponse2008(name='resource::' + nsd["name"] + '::' + nsd["version"], state='PUBLISHED'))

    return almTypes


def types_name_get(name):
    """
    Get descriptor of a resource types
    Returns information about a specific resource type,
    including its YAML descriptor.
    :param name: Unique name for the resource type requested
    :type name: str

    :rtype: List[InlineResponse2009]
    """
    """
    name: \"resource::hello-world::1.0\"\n
    description: \"A sample resource\"\n
    lifecycle:\n- \"Install\"\n
    resource-manager-type: \"ansible-rm\"\n",
    """

    osmNsd = OsmClient().getNsd()

    # get the NSD name
    nsdName = name.split('::')[1]

    try:
        # get an OSM network service descriptors (NSD)
        app.logger.info('fetching NSD ' + nsdName)
        osmNsd = osmNsd.get(nsdName)
    except NotFound as err:
        app.logger.error("Type not found: {0}".format(err))
        abort(404, str(err))

    # build resource descriptor
    props = {}
    # get all VLDs and add them as read-only _properties
    # this enables other resources to attach to these networks
    for vld in list(osmNsd["vld"]):
        item = {vld["id"]+'_name': {"type": "string", "description": "OS network name", "read-only": True}}
        props.update(item)
    # add props to refernce the OSM NS
    item = {"ns_id": {"type": "string", "description": "OSM NS uuid", "read-only": True}}
    props.update(item)
    item = {"ns_name": {"type": "string", "description": "OSM NS name", "read-only": True}}
    props.update(item)

    # only supported lifecycle operatiosn are install and uninstall
    # no start/stop/configure. There is a scale but this cannot be propagated from ALM down to osm
    lf = ['Install', 'Uninstall']
    rd = { "name": name, "description": osmNsd["description"],"properties": props, "lifecycle": lf, "resource-manager-type": "osm-rm" }
    rdy = yaml.dump(rd, explicit_start=True, default_flow_style=False)

    return InlineResponse2009(name=name, state='PUBLISHED', descriptor=rdy)
