import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logs_dir = Path("logs")
logs_dir.mkdir(parents=True, exist_ok=True)
logger.addHandler(logging.FileHandler(logs_dir/'main.log'))
logger.setLevel(logging.DEBUG)

logger.info('Logger created')