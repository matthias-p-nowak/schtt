#!/usr/bin/python3.9
import atexit
import logging
import jinja2
import yaml
import sys

cfg = {}
defaultCFG = """
---
endpoint:
    host: localhost
    port: 5060
"""


def main():
    """
    Use scht.py <config file>
    """
    global cfg
    if len(sys.argv) < 2:
        print(main.__doc__)
        sys.exit(2)
    cfg = yaml.safe_load(defaultCFG)
    cfg_file = sys.argv[1]
    with open(cfg_file) as cf:
        cfg2=yaml.safe_load(cf)
        if cfg2 is not None:
            cfg.update(yaml.safe_load(cf))
    logging.debug("ended")

if __name__ == '__main__':
    atexit.register(print, 'good bye')
    logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w',
                        format='%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d %(funcName)s: %(message)s', )
    logging.debug('started')
    main()
