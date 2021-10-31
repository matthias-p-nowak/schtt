#
""""
Place for utility modules
"""
import logging

import tester


def add_data(tr: tester.TestRun, stepdata: dict, step: int, td: dict) -> int:
    logging.debug(f'running step {step}')
    try:
        data=stepdata['data']
        for k in data:
            keys=k.split('.')
            val=tr.data
            for k2 in keys[:-1]:
                if k2 not in val:
                    val[k2]={}
                val=val[k2]
            val[keys[-1]]=data[k]
    except Exception as ex:
        s=f'got an exception {type(ex)} {ex}'
        logging.error(s)
        raise BaseException(s)
    return step+1

def initialize():
    logging.debug("initializing utilities")
    tester.add_action_module('data',add_data)
