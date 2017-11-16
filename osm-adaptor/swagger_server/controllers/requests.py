"""
manage resource instance transition requests

IBM Corporation, 2017, jochen kappel
"""

import json
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from swagger_server.models.inline_response202 import InlineResponse202
from flask import current_app as app

from .driver_config import ConfigReader
from .cassandra import CassandraHandler
from .asm_osmclient import OsmClient
from osmclient.common.exceptions import NotFound
from osmclient.common.exceptions import ClientException
from .kafka import *

class RequestHandler():
    """
    request handler
    """
    def __init__(self):
        self.logger = app.logger
        self.config = ConfigReader()
        self.logger.info('initializing request handler')
        self.dbsession = CassandraHandler().get_session()
        self.osm_client = OsmClient()

    def runOsmTransition(self):
        osmNs = self.osm_client.getNs()
        self.logger.info('get the network service handler')

        if self.transitionRequest.transition_name == 'Install':
            try:
                # create a NS instance
                self.logger.info('creating the network service')
                self.log_request_status('IN_PROGRESS', 'sending request to OSM', '')
                self.logger.debug('type ' + self.transitionRequest.resource_type.split('::')[1])
                self.logger.debug('name ' + self.transitionRequest.resource_name)
                self.logger.debug('loc ' + self.transitionRequest.deployment_location)
                osmNs.create(nsd_name=self.transitionRequest.resource_type.split('::')[1],
                             nsr_name=self.transitionRequest.resource_name,
                              account=self.transitionRequest.deployment_location,
                              description='Install request from ALM')

            except (ClientException, NotFound) as err:
                self.logger.error(str(err))
                self.log_request_status('FAILED', str(err), '')

            try:
                # get NS id
                self.logger.info('getting network service id')
                self.log_request_status('IN_PROGRESS', 'requesting NS id from OSM', '')
                ns = osmNs.get(self.transitionRequest.resource_name)
                ns_id = ns["id"]
                self.logger.debug('resource (ns) id ' + ns_id)
                self.log_request_status('COMPLETED', 'NS created', ns_id)

                # create properties and internal resources
                props = {"ns_name": self.transitionRequest.resource_name, "ns_id": ns_id}
                internal_resources = []
                # add VLDs
                for vld in list(ns["nsd"]["vld"]):
                    item = {"name": vld["name"], "type": vld["type"], "id":vld["id"]}
                    internal_resources.append(item)
                    itemprop = {vld["id"]+'_name': self.transitionRequest.resource_name + '.' + vld["id"] }
                    props.update(itemprop)
                self.logger.debug("properties: " + str(props))
                self.logger.debug("internal resources: " + str(internal_resources))

                self.create_instance(ns_id, props, internal_resources)
            except (ClientException, NotFound) as err:
                self.logger.error(str(err))
                self.log_request_status('FAILED', str(err), '')

        elif self.transitionRequest.transition_name == 'Uninstall':
            try:
                # get NS id
                self.logger.info('getting network service id')
                self.log_request_status('IN_PROGRESS', 'requesting NS id from OSM', '')
                ns_id = osmNs.get_field(self.transitionRequest.resource_name, 'id')
                # remove NS instance
                osmNs.delete(ns_name=self.transitionRequest.resource_name, wait=False)
                self.log_request_status('COMPLETED', 'NS deleted', ns_id)
                self.logger.info('NS removed')
                self.delete_instance(ns_id, self.transitionRequest.deployment_location)
            except ClientException as err:
                self.logger.error(str(err))
                self.log_request_status('FAILED', str(err), '')

        elif self.transitionRequest.transition_name == 'Integrity':
            try:
                # check operational state NS instance
                self.log_request_status('IN_PROGRESS', 'sending request to OSM', '')
                osmNsStatus = osmNs.get_field(self.transitionRequest.resource_name, 'operational-status')
                if osmNsStatus != 'running':
                    pass
            except ClientException as err:
                self.logger.error(str(err))
                self.log_request_status('FAILED', str(err), '')

        else:
            self.log_request_status('FAILED', 'operation not supported', '')

        return

    def start_request(self, tr):
        """
        start a request i.e. run an ansible playbook_dir
        """
        self.transitionRequest = tr
        # create request id
        self.request_id = uuid.uuid1()
        self.logger.debug('creating request with id: ' + str(self.request_id))
        self.started_at = datetime.now()

        # do some checks
        self.logger.info('transition request received')
        self.logger.debug('transition action: ' + self.transitionRequest.transition_name )

        # check resource type
        self.logger.info('validating requeste resource type: ' + self.transitionRequest.resource_type)
        try:
            self.osm_client.getNsd().get(self.transitionRequest.resource_type.split('::')[1])
        except NotFound as e:
            self.logger.error('invalid resource type: ' + self.transitionRequest.resource_type + ' ' + str(e) )
            resp = InlineResponse202(str(self.request_id), 'FAILED', self.config.getSupportedFeatures())
            self.logger.info('request ' + str(self.request_id) + ' FAILED: ' + str(e))
            return 404, resp

        # check location exists
        self.logger.info('validate location: ' + self.transitionRequest.deployment_location)
        try:
            self.osm_client.getVim().get(self.transitionRequest.deployment_location)
        except NotFound as e:
            self.logger.error('location ' + self.transitionRequest.deployment_location + ' ' + str(e))
            resp = InlineResponse202(str(self.request_id), 'FAILED', self.config.getSupportedFeatures())
            self.logger.info('request ' + str(self.request_id) + ' FAILED: ' + str(e))
            return 404, resp

        self.logger.info('async OSM transaction started')

        with app.app_context():
            executor = ThreadPoolExecutor(max_workers=4)
            executor.submit(self.runOsmTransition)

            #self.runOsmTransition()

            self.logger.debug('transition request ' + str(self.transitionRequest))
            self.log_request_status('PENDING', 'playbook initialized', '')
            self.logger.info('request ' + str(self.request_id) + ' PENDING ')
            resp = InlineResponse202(str(self.request_id), 'PENDING', self.config.getSupportedFeatures())
            return 202, resp

    def get_request(self, requestId):
        """
        get request from db
        """

        pload = {}
        app.logger.info('reading request status from db')

        if requestId:
            requestId = uuid.UUID(requestId)
        else:
            app.logger.error('request id missing')
            return 400, 'must provide request id', ''

        app.logger.info('request fetched from DB: ' + str(requestId))
        query = "SELECT requestId, requestState, requestStateReason, resourceId, startedAt, finishedAt FROM requests WHERE requestId = %s"
        rows = self.dbsession.execute(query, [requestId])

        if rows:
            pload = {}
            for row in rows:
                pload['requestId'] = str(requestId)
                pload['startedAt'] = row['startedat'].strftime('%Y-%m-%dT%H:%M:%SZ')
                pload['requestStateReason'] = row['requeststatereason']
                pload['requestState'] = row['requeststate']
                if row['finishedat'] is not None:
                    pload['finishedAt'] = row['finishedat'].strftime('%Y-%m-%dT%H:%M:%SZ')
                else:
                    pload['finishedAt'] = ''
                if row['resourceid'] is not None:
                    pload['resourceId'] = str(row['resourceid'])
                else:
                    pload['resourceId'] = ''
                app.logger.debug('request status is: ' + json.dumps(pload))
                return 200, '', pload
        else:
            app.logger.info('no request found for id: '+str(requestId))
            return 404, '', ''

    def log_request_status(self, status, reason, resource_id):
        """
        write log status to db or push to kafka
        """
        self.logger.info('working on status '+status)
        is_async_mode = self.config.getSupportedFeatures()['AsynchronousTransitionResponses']
        ttl = self.config.getTTL()

        self.logger.info('async request mode is ' + str(is_async_mode))
        if (status == 'COMPLETED') or (status == 'FAILED'):
            self.finished_at = datetime.now()
            finished = self.finished_at.strftime('%Y-%m-%dT%H:%M:%SZ')
            self.logger.debug('request finished at ' + finished)
        else:
            finished = ''

        started = self.started_at.strftime('%Y-%m-%dT%H:%M:%SZ')

        self.logger.info('resrouce id ' + resource_id)
        if resource_id != '':
            resource_id = uuid.UUID(resource_id)
            self.logger.info('converted resrouce id ' + str(resource_id))
        else:
            resource_id = None

        self.logger.info('writing request status to db')
        self.logger.debug('request id '+str(self.request_id))

        try:
            if status == 'PENDING':
                self.dbsession.execute(
                    """
                    INSERT INTO requests (requestId, requestState, requestStateReason,startedAt, context)
                    VALUES  (%s, %s, %s, %s, %s)
                    USING TTL """ + str(ttl) + """
                    """,
                    (self.request_id, status, reason, started, self.config.getSupportedFeatures())
                    )
            else:
                self.dbsession.execute(
                    """
                    INSERT INTO requests (requestId, requestState, requestStateReason, resourceId, finishedAt)
                    VALUES  (%s, %s, %s, %s, %s)
                    USING TTL """ + str(ttl) + """
                    """,
                    (self.request_id, status, reason, resource_id, finished)
                    )
        except Exception as err:
            # handle any other exception
            self.logger.error(str(err))
            raise

        self.logger.info('request logged to DB: ' + str(self.request_id))

        if is_async_mode:
            if (status == 'COMPLETED') or (status == 'FAILED'):
                # call kafka
                self.logger.info('async mode and status is '+status)
                kafkaClient = Kafka(self.logger)

                kmsg = {}
                kmsg['resourceInstance'] = dict(self.resInstance)
                kmsg['requestId'] = str(self.request_id)
                kmsg['resourceManagerId'] = self.transition_request.resource_manager_id
                kmsg['deploymentLocation'] = self.transition_request.deployment_location
                kmsg['resourceType'] = self.transition_request.resource_type
                kmsg['transitionName'] = self.transition_request.transition_name
                kmsg['context'] = {}
                kmsg['requestState'] = status
                kmsg['requestStateReason'] = reason
                kmsg['startedAt'] = started
                kmsg['finishedAt'] = finished

                self.logger.debug('sending message to kafka: ' + str(kmsg))
                kafkaClient.sendLifecycleEvent(kmsg)

        return

    def create_instance(self, resource_id, out_props, internal_resources):
        """
        save instance details to db
        """
        self.logger.info('create instance  ' + resource_id)

        # a little cheating, need to get this from OS
        created_at = self.started_at.strftime('%Y-%m-%dT%H:%M:%SZ')
        last_modified_at = created_at

        pitem = {'resourceId': resource_id,
                 'deploymentLocation': self.transitionRequest.deployment_location,
                 'resourceType': self.transitionRequest.resource_type,
                 'resourceName': self.transitionRequest.resource_name,
                 'resourceManagerId': self.transitionRequest.resource_manager_id,
                 'properties': out_props,
                 'internalResourceInstances': internal_resources,
                 'metricKey': self.transitionRequest.metric_key,
                 'createdAt': created_at,
                 'lastModifiedAt': last_modified_at
                 }
        try:
            self.dbsession.execute("""
                INSERT INTO instances
                (resourceId, resourceType, resourceName, resourceManagerId,
                deploymentLocation, createdAt, lastModifiedAt,
                properties, internalResourceInstances, metricKey)
                VALUES  (%s, %s, %s, %s, %s, %s, %s,%s, %s, %s)
                """,
                (uuid.UUID(pitem['resourceId']), pitem['resourceType'],
                pitem['resourceName'], pitem['resourceManagerId'],
                pitem['deploymentLocation'], pitem['createdAt'],
                pitem['lastModifiedAt'], pitem['properties'],
                pitem['internalResourceInstances'], pitem['metricKey'])
            )
        except Exception as err:
            # handle any other exception
            self.logger.error(str(err))
            raise

        self.logger.info('instance logged to DB: ' + str(pitem['resourceId']))
        self.logger.debug('instance created ' + str(pitem))
        return pitem

    def delete_instance(self, resource_id, deployment_location):
        """
        delete instance details from db
        """
        self.logger.info('deleting instance  ' + resource_id)

        try:
            self.dbsession.execute("""
                DELETE FROM instances
                WHERE resourceid = %s and deploymentLocation = %s
                """,
                [uuid.UUID(resource_id), deployment_location]
            )
        except Exception as err:
            # handle any other exception
            self.logger.error(str(err))
            raise

        self.logger.debug('instance deleted ' + resource_id)
        return
