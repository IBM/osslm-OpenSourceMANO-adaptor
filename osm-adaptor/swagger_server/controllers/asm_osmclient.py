"""
Wraps the OSM client modules

IBM Corporation, 2017, jochen kappel
"""

from flask import current_app as app
from .driver_config import ConfigReader
from osmclient.v1 import client
from osmclient.common.exceptions import NotFound
from osmclient.common.exceptions import ClientException


class OsmClient:
    """
    OSM client singleton
    """
    class __OsmClient:
        """ inner class, wrapper aroudn the osmclient library """

        def __init__(self):
            self.logger = app.logger
            self.logger.info('initializing OSM client libs')
            self.config = ConfigReader()

            osmHost = self.config.getOsmHost()
            app.logger.info("getting osm client for OSM server " + osmHost)

            self.osmClient = client.Client(osmHost)
            app.logger.info("connected to OSM")

        def setRequestData(self, location, request_id, started_at,
                           dbsession, tr):
            self.logger.info('initializing osm executor')

            self.dbsession = dbsession
            self.transition_request = tr

            self.location = location
            self.logger.debug(str(self.location))

            self.request_id = request_id
            self.started_at = started_at
            self.finished_at = None
            self.resInstance = {}

        def getVim(self):
            """ get the VIM handle """
            return self.osmClient.vim

        def getNsd(self):
            """ get the NSD handle """
            return self.osmClient.nsd

        def getNs(self):
            """ get the NS handle """
            return self.osmClient.ns

    instance = None

    def __init__(self):
        if not OsmClient.instance:
            OsmClient.instance = OsmClient.__OsmClient()

    def __getattr__(self, name):
        return getattr(self.instance, name)
