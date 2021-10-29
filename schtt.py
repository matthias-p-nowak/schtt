#!/usr/bin/python3.9
import atexit
import logging
import sys

import config
import tester
import transport



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
        transport.initialize()
        tester.run_tests(sys.argv[2:])
    except Exception as ex:
        print(f'program aborted due to an exception {ex}')
    finally:
        logging.debug("ended")

if __name__ == '__main__':
    atexit.register(print, 'good bye')
    logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w',
                        format='%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d %(funcName)s: %(message)s', )
    logging.debug('started')
    main()
