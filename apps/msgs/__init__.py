import logging

logger = logging.getLogger('apps.msgs')
logging.getLogger('dramatiq').addHandler(logger)
