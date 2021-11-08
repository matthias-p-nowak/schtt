#!/usr/bin/python3.9
"""
simple ch testing tool, main entry
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
    Use schtt.py <config file> [test1 | test1 test2 ...]
    The first file is a configuration file in yaml format
    The following arguments are either files or directories that contain tests to run
    """
    try:
        # check missing argument
        if len(sys.argv) < 2:
            print(main.__doc__)
            sys.exit(2)
        # getting configuration
        cfg_file = sys.argv[1]
        with open(cfg_file) as cf:
            config.update_config(cf)
        dbl=config.get_config('debug',logging.ERROR)
        # logging, logging pattern for idea
        # ^([0-9-\s:,]+)\s+\[(\w+)]\s+([^\s]+)\s([\w:<>]+)+(.+)$
        logging.basicConfig(filename='debug.log', level=dbl, filemode='wt',
                            format='%(asctime)s [%(levelname)s]\t%(pathname)s:%(lineno)d\t%(funcName)s: %(message)s', )
        # initializing
        siptr.initialize()
        util.initialize()
        siphandler.initialize()
        # running tests
        tester.run_tests(sys.argv[2:])
    except Exception as ex:
        print(f"program aborted due to an exception {ex}")
    finally:
        # close connections
        siptr.shutdown()
        logging.debug("ended")


if __name__ == '__main__':
    """entry point for main"""
    atexit.register(print, "good bye")
    # startup done, doing main
    main()
