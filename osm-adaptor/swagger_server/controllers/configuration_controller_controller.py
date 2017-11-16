"""
configuration controller
- get config properties

IBM Corporation, 2017, jochen kappel
"""
import connexion
from swagger_server.models.inline_response2007 import InlineResponse2007
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime

# business logic imports
from flask import abort
from .driver_config import ConfigReader

def configuration_get():
    """
    Get Resource Manager Configuration.
    Returns high-level information about the configuration of this Resource Manager.

    :rtype: InlineResponse2007
    """

    try:
        cfg = ConfigReader()
        drvName, drvVer = cfg.getDriverNameVersion()
        supportedFeatures = cfg.getSupportedFeatures()
        supportedApiVersions = cfg.getSupportedApiVersions()
        supportedProperties = cfg.getDriverProperties(None)
    except FileNotFoundError:
        abort(404, 'configuration not found')


    resp200 = InlineResponse2007(drvName, drvVer, supportedApiVersions, supportedFeatures, supportedProperties)
    return resp200
