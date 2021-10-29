import logging
import pprint

import config


def initialize():
    logging.debug("initializing transport")
    val = config.get_config('endpoints', [])
    pprint.pprint(val)
