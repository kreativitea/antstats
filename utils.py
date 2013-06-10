import os
import yaml
from collections import deque

def open_log(log_name):
    ''' Opens a specific log as an iterable.  Atomic file operation. '''
    path = os.path.join(os.getcwd(), 'logs', log_name)
    f = open(path)
    with f:
        d = deque(f)
        return iter(d)


def list_log_names():
    ''' Returns a list of all log files in the logs directory. '''
    path = os.path.join(os.getcwd(), 'logs')
    return os.listdir(path)


def load_config():
    f = open('whore.yaml')
    with f:
        return yaml.load(f)
