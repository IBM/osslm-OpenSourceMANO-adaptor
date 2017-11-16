"""
Resrouce manager utilities

IBM Corporation, 2017, jochen kappel
"""
import connexion
from swagger_server.models.deployment_location1 import DeploymentLocation
from swagger_server.models.inline_response20011 import InlineResponse20011
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime

from flask import abort
from flask import current_app as app
from .cassandra import CassandraHandler


def database_delete():
    """
    deletes all database tables
    deletes database tables (intances, resources, locations) !!!

    :rtype: None
    """
    rcode = CassandraHandler().delete_tables()
    if rcode == 200:
        return 200
    else:
        abort(rcode, '')


def database_post():
    """
    create database tables
    creates all required database tables (intances, resources, locations)

    :rtype: None
    """
    rcode = CassandraHandler().create_tables()
    if rcode == 201:
        return 201
    else:
        abort(rcode, '')


def database_table_patch(table):
    """
    truncates a given database table
    deletes all content from a database table (intances, resources, locations !!)
    :param table: Table (instances, resources, locations)
    :type table: str

    :rtype: None
    """
    rcode = CassandraHandler().truncate_table(table)
    if rcode == 200:
        return 200
    else:
        abort(rcode, '')


def topology_deployment_locations_properties_get():
    """
    get list of deployment locations with all properties
    Returns a list of all deployment locations available to this Resource Manager

    :rtype: List[InlineResponse20011]
    """
    return 'do some magic!'
