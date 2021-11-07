"""
contains the sip related actions
"""
import logging

import sipmsg
import tester
import util


def do_sipout(tr: tester.TestCaseRun, stepdata: dict, step: int, td: dict) -> int:
    logging.debug(f'step {step} - sipout')
    f = td['logf']
    print(f'----- step {step} - sending sip -----', file=f)
    data = {}
    util.merge(tr.data, data)
    util.merge({'t': td}, data)
    fl = stepdata['firstline']
    hdrs = stepdata['headers']
    body = ''
    if 'body' in stepdata:
        body = stepdata['body']
    con = stepdata['connection']
    je = util.jinjaEnv
    fl = je.from_string(fl).render(data)
    hdrs = je.from_string(hdrs).render(data)
    body = je.from_string(body).render(data)
    sm = sipmsg.SipMessage(fl, hdrs, body)
    return step + 1


def initialize():
    try:
        logging.info('initializing siphandler')
        tester.add_action_module('sipout', do_sipout)
    except Exception as ex:
        logging.error(f"got an exception {ex}")
