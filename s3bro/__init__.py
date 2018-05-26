import logging


def loglevel(level):
    if "ERROR" == level:
        logging.basicConfig(level=logging.ERROR)
    if 'DEBUG' == level:
        logging.basicConfig(level=logging.DEBUG)
    if 'INFO' == level:
        logging.basicConfig(level=logging.INFO)
    if 'WARNING' == level:
        logging.basicConfig(level=logging.WARNING)
