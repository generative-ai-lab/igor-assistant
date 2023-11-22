import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.FileHandler('logs/main.log'))
logger.setLevel(logging.DEBUG)

logger.info('Logger created')