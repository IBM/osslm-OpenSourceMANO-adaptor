"""
Database functions (create schema, connect,..)

IBM Corporation, 2017, jochen kappel
"""

from flask import current_app as app
from cassandra.cluster import Cluster
from cassandra.query import dict_factory


class CassandraHandler:
    """
    database handler singleton
    """
    class __CassandraHandler:
        """ inner signelton class"""
        def __init__(self):
            self.keyspace = "alm_osm"
            self.dbSession = None

        def __del__(self):
            self.dbSession.close()

        def get_session(self):
            """ get a DB conenction """
            if self.dbSession:
                app.logger.info('using cassandra session to ' + self.keyspace)
            else:
                app.logger.info('creating cassandra session ' + self.keyspace)

                try:
                    self.cluster = Cluster(['alm-osm-rm-db'])

                    self.dbSession = self.cluster.connect()
                    app.logger.info('connected to cassandra, keyspace: ' + self.keyspace)
                except ConnectionRefusedError as err:
                    app.logger.error("No connection error: {0}".format(err))
                    self.dbSession = None
                    raise
                except Exception as e:
                    # handle any other exception
                    self.dbSession = None
                    app.logger.error(str(e))
                    raise

                else:
                    self.dbSession.execute("""
                        CREATE KEYSPACE IF NOT EXISTS %s
                        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
                        """ % self.keyspace)

                    self.dbSession.set_keyspace(self.keyspace)
                    self.dbSession.row_factory = dict_factory

            return self.dbSession

        def create_tables(self):
            """
            creates all RM tables
            requests
            instances
            """
            session = self.get_session()

            try:
                session.execute("""
                CREATE TABLE  IF NOT EXISTS requests (
                    requestId UUID,
                    requestState text,
                    requestStateReason text,
                    resourceId UUID,
                    startedAt timestamp,
                    finishedAt timestamp,
                    context map<text, boolean>,
                    PRIMARY KEY ( (requestId) ))
                    """)
                app.logger.info('table requests created')
            except Exception as e:
                # handle any other exception
                app.logger.error(str(e))
                return 400

            try:
                session.execute("""
                CREATE TABLE IF NOT EXISTS instances (
                    resourceId UUID,
                    resourceType text,
                    resourceName text,
                    resourceManagerId text,
                    deploymentLocation text,
                    metricKey text,
                    createdAt timestamp,
                    lastModifiedAt timestamp,
                    properties map<text, text>,
                    internalResourceInstances list<frozen <map <text, text>>>,
                    PRIMARY KEY ( ( deploymentLocation ), resourceId  ))
                    """)
                app.logger.info('table instances created')
                session.execute("""
                    CREATE INDEX IF NOT EXISTS idx_instances_id
                    ON instances ( resourceId )
                    """)

                session.execute("""
                    CREATE INDEX IF NOT EXISTS idx_instances_type
                    ON instances ( resourceType )
                    """)

                session.execute("""
                    CREATE INDEX IF NOT EXISTS idx_instances_props
                    ON instances ( properties )
                    """)

            except Exception as e:
                # handle any other exception
                app.logger.error(str(e))
                return 400

            return 201

        def delete_tables(self):
            """
            deletes all tables and indeces
            """
            session = self.get_session()

            try:
                session.execute("DROP INDEX IF EXISTS idx_instances_id")
                session.execute("DROP INDEX IF EXISTS idx_instances_type")
                session.execute("DROP INDEX IF EXISTS idx_instances_props")
                session.execute("DROP TABLE IF EXISTS alm_osm.instances")
                app.logger.info('table instances deleted')
            except Exception as e:
                # handle any other exception
                app.logger.error(str(e))
                return 400

            try:
                session.execute("DROP TABLE  IF EXISTS alm_osm.requests")
                app.logger.info('table requests deleted')
            except Exception as e:
                # handle any other exception
                app.logger.error(str(e))
                return 400

            return 200

        def truncate_table(self, tablename):
            """
            truncates a table
            """
            session = self.get_session()

            try:
                session.execute("TRUNCATE TABLE " + tablename)
                app.logger.info('table '+tablename+' truncated')
            except Exception as e:
                # handle any other exception
                app.logger.error(str(e))
                return 404

            return 200

    instance = None

    def __init__(self):
        if not CassandraHandler.instance:
            CassandraHandler.instance = CassandraHandler.__CassandraHandler()

    def __getattr__(self, name):
        return getattr(self.instance, name)
