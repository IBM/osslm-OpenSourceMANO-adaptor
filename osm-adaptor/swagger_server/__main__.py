#!/usr/bin/env python3

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from distutils.dir_util import copy_tree
from os.path import dirname, abspath
import connexion
from .encoder import JSONEncoder
from .controllers.driver_config import ConfigReader

if __name__ == '__main__':
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = JSONEncoder

    log_level = logging.getLevelName(os.environ.get('LOG_LEVEL'))
    if not log_level:
        log_level = 'INFO'
    log_dir = os.environ.get('LOG_FOLDER')
    if not log_dir:
        log_dir = '.'
    else:
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    # this is set by the dockerfile
    formatter = logging.Formatter("[%(asctime)s] {%(module)s:%(lineno)d} %(levelname)s - %(message)s")
    handler = TimedRotatingFileHandler(log_dir + '/almOsmDriverLog', when='midnight', interval=1, backupCount=7)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)
    app.app.logger.addHandler(handler)
    app.app.logger.setLevel(log_level)

    app.add_api('swagger.yaml', arguments={'title': 'OSM resource manager specification.'})
    app.app.logger.info('driver starting listening on port 8081')
    app.run(port=8081)
