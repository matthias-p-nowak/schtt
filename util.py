#
""""
Place for utility modules
"""
import logging
import pprint

import jinja2
import yaml

import tester

jinjaEnv = jinja2.Environment()


def get_data(key: str, data: dict):
    keys = key.split('.')
    d = data
    for k in keys:
        if k == '':
            continue
        d = d[k]
    return d

def merge(source, dest):
  for key in source:
    value=source[key]
    if key not in dest:
      dest[key]=value
    elif isinstance(value, dict):
      merge(value,dest[key])
    elif isinstance(value,list):
      dest[key] += value
    else:
      dest[key]=value

def add_data(tr: tester.TestRun, stepdata: dict, step: int, td: dict) -> int:
    logging.debug(f'step {step} - adding data')
    f = td['logf']
    print(f'----- step {step} - adding data -----', file=f)
    try:
        data = stepdata['data']
        for k in data:
            keys = k.split('.')
            val = tr.data
            for k2 in keys[:-1]:
                if k2 not in val:
                    val[k2] = {}
                val = val[k2]
            val[keys[-1]] = data[k]
    except Exception as ex:
        s = f'got an exception {type(ex)} {ex}'
        logging.error(s)
        raise BaseException(s)
    return step + 1


def debug_var(tr: tester.TestRun, stepdata: dict, step: int, td: dict) -> int:
    logging.debug(f'step {step} - debug variable')
    key = stepdata['variable']
    f = td['logf']
    print(f'----- step {step} debug output of "{key}":', file=f)
    data={}
    merge(tr.data,data)
    merge({'t':td},data)
    d = get_data(key, data)
    pprint.pprint(d,stream=f,indent=4)
    print('----- end -----', file=f)
    return step + 1


def initialize():
    logging.debug("initializing utilities")
    tester.add_action_module('data', add_data)
    tester.add_action_module('debug', debug_var)
