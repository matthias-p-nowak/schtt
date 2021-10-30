""""
Testing infrastructure
"""
import concurrent.futures.thread
import logging
import os
import pprint
import threading

import yaml

import config


class TestRun():
    def __init__(self, tpe: concurrent.futures.thread.ThreadPoolExecutor, test, sem: threading.Semaphore):
        self.running = True
        self.tpe = tpe
        self.test = test
        self.sem = sem

    def run_test(self):
        try:
            tn = 'test-not-named'
            if 'name' in self.test:
                tn = self.test['name']
            else:
                self.test['name'] = tn
            fn = self.test['filename']
            future_threads = []
            logging.info(f'running test {fn} -> {tn}')
            if 'threads' not in self.test or not isinstance(self.test['threads'], list):
                logging.error(f' no defined threads in {fn}->{tn}')
                return
            for t in self.test['threads']:
                res = self.tpe.submit(self.run_thread, t)
                future_threads.append(res)
            concurrent.futures.wait(future_threads)
        except Exception as ex:
            logging.error(f' got an exception {ex}')
        finally:
            self.sem.release()

    def run_thread(self, t):
        try:
            tn = self.test['name']
            fn = self.test['filename']
            if 'name' in t:
                trn = t['name']
            else:
                trn = 'unnamed thread'
            logging.info(f'running thread {trn} for {fn}->{tn}')
            pprint.pprint(t)
        except Exception as ex:
            logging.error(f' got an exception in run_thread {ex}')


def get_all_tests(items: list[str]):
    for it in items:
        for dirpath, dirnames, filenames in os.walk(it):
            for fn in filenames:
                ffn = os.path.join(dirpath, fn)
                with open(ffn) as inp:
                    tt = yaml.safe_load(inp)
                    if isinstance(tt, list):
                        for t in tt:
                            if not isinstance(t, dict):
                                t_str = pprint.pformat(t)
                                logging.error(f'file {ffn} contains an error with {t_str}')
                                continue
                            t['filename'] = ffn
                            yield t
                    else:
                        if not isinstance(tt, dict):
                            t_str = pprint.pformat(t)
                            logging.error(f'file {ffn} contains an error with {t_str}')
                            continue
                        tt['filename'] = ffn
                        yield tt


def run_tests(tests: list[str]):
    logging.debug("running tests")
    num_concurrent = config.get_config('concurrent', 1)
    sem_limit = threading.Semaphore(num_concurrent)
    with concurrent.futures.ThreadPoolExecutor() as tpe:
        for t in get_all_tests(tests):
            sem_limit.acquire()
            tr = TestRun(tpe, t, sem_limit)
            res = tpe.submit(tr.run_test)
        for i in range(num_concurrent):
            sem_limit.acquire()
        logging.info('clear for shutdown')
    print('all tests done')
