import logging
from rich.logging import RichHandler
from config.settings import config

def setup_logger(name):
    logger = logging.getLogger(name)
    level = getattr(logging, config.get('logging.level', 'INFO'))
    logger.setLevel(level)
    
    # Console handler with Rich
    ch = RichHandler(rich_tracebacks=True, markup=True)
    ch.setLevel(level)
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    fh = logging.FileHandler(config.get('logging.file', 'aegis.log'))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)
    
    return logger

logger = setup_logger('AegisBreach')