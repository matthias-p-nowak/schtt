#!/usr/bin/python3.9
import atexit
import logging
import jinja2
import yaml
import sys
import concurrent.futures.thread

cfg = {}
defaultCFG = """
---
endpoint:
  - name: rhino
    host: localhost
    port: 5060
concurrent: 5
tests:
  tests:
"""
ttpe: concurrent.futures.thread.ThreadPoolExecutor = None
itpe: concurrent.futures.thread.ThreadPoolExecutor = None

def main():
    """
    Use scht.py <config file>
    """
    global cfg,ttpe,itpe
    if len(sys.argv) < 2:
        print(main.__doc__)
        sys.exit(2)
    cfg = yaml.safe_load(defaultCFG)
    cfg_file = sys.argv[1]
    with open(cfg_file) as cf:
        cfg2=yaml.safe_load(cf)
        if cfg2 is not None:
            cfg.update(yaml.safe_load(cf))
    # a threadpoolexecutor for the infrastructure
    itpe=concurrent.futures.thread.ThreadPoolExecutor()
    # only for the tests
    with concurrent.futures.thread.ThreadPoolExecutor() as exec:
        ttpe=exec

    logging.debug("ended")

if __name__ == '__main__':
    atexit.register(print, 'good bye')
    logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w',
                        format='%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d %(funcName)s: %(message)s', )
    logging.debug('started')
    main()
