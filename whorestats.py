import logging

from utils import load_config

config = load_config('whore.cfg')
logconfig = load_config('log.cfg')
    
logging.basicConfig(level=logging.DEBUG, **logconfig)

logger = logging.getLogger(__name__)