#!/usr/bin/python3.9
"""
simple ch testing tool
"""
import atexit
import logging
import sys

import config
import siphandler
import siptr
import tester
import util


def main():
    """
    Use schtt.py <config file>
    """
    global cfg
    try:
        if len(sys.argv) < 2:
            print(main.__doc__)
            sys.exit(2)
        cfg_file = sys.argv[1]
        with open(cfg_file) as cf:
            config.update_config(cf)
        siptr.initialize()
        util.initialize()
        siphandler.initialize()
        tester.run_tests(sys.argv[2:])
    except Exception as ex:
        print(f'program aborted due to an exception {ex}')
    finally:
        siptr.shutdown()
        logging.debug("ended")


if __name__ == '__main__':
    atexit.register(print, 'good bye')
    # ^([0-9-\s:,]+)\s+\[(\w+)]\s+([^\s]+)\s([\w:<>]+)+(.+)$
    logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='wt',
                        format='%(asctime)s [%(levelname)s]\t%(pathname)s:%(lineno)d\t%(funcName)s: %(message)s', )
    logging.debug('started')
    main()
