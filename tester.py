""""
Testing infrastructure
"""
import concurrent.futures.thread
import logging
import os
import pprint
import threading
from datetime import datetime
from typing import Callable

import yaml

import config


class TestCaseRun:
    running: bool
    data = {}

    def __init__(self, tpe: concurrent.futures.thread.ThreadPoolExecutor, testcase:dict, sem: threading.Semaphore):
        self.running = True
        """stop all loops when test case is no longer running"""
        self.tpe = tpe
        """use this ThreadPoolExecutor for threads"""
        self.testcase = testcase
        """Test case to try"""
        self.sem = sem
        """when test case is done, release this semaphore 
            - it is used to limit the number of concurrent test case executions"""
    def run_testcase(self):
        """Runs a single testcase"""
        try:
            tn = 'test-not-named'
            if 'name' in self.testcase:
                tn = self.testcase['name']
            else:
                self.testcase['name'] = tn
            fn = self.testcase['filename']
            future_threads = []
            logging.info(f'running test {fn} -> {tn}')
            pp = os.path.join('logs', fn)
            os.makedirs(pp, exist_ok=True)
            logf = open(os.path.join(pp, tn + '.txt'), 'wt')
            now = datetime.now().strftime('%Y-%m-%d %X')
            print(f'tested at {now}', file=logf)
            if 'threads' not in self.testcase or not isinstance(self.testcase['threads'], list):
                logging.error(f' no defined threads in {fn}->{tn}')
                return
            for t in self.testcase['threads']:
                ttr=TestThreadRun(self, t)
                res = self.tpe.submit(self.run_thread, t)
                future_threads.append(res)
            concurrent.futures.wait(future_threads)
        except Exception as ex:
            logging.error(f' got an exception {ex}')
        finally:
            self.sem.release()
            if logf is not None:
                logf.close()

    def run_thread(self, t):
        global action_modules
        try:
            tn = self.testcase['name']
            fn = self.testcase['filename']
            if 'name' in t:
                trn = t['name']
            else:
                trn = 'unnamed thread'
            logging.info(f'running thread {trn} for {fn}->{tn}')
            pp = os.path.join('logs', fn, tn)
            os.makedirs(pp, exist_ok=True)
            logf = open(os.path.join(pp, trn + ".txt"), 'wt')
            t['logf'] = logf
            idx = 0
            while self.running:
                if idx >= len(t['actions']):
                    break;
                step = t['actions'][idx]
                action = step['action']
                if action not in action_modules:
                    s = f'action "{action}" is not implemented'
                    logging.error(s)
                    print(s, file=logf)
                    raise NotImplementedError(s)
                idx = action_modules[action](self, step, idx, t)
            pprint.pprint(t)
        except Exception as ex:
            logging.error(f' got an exception in run_thread {type(ex)}:{ex}')
            raise ex
        finally:
            if logf is not None:
                logf.close()


class TestThreadRun:
    data = {}

    def __init__(self,tc: TestCaseRun, t:dict):
        self.parent=tc
        self.data.update(tc.data)
        pass
    def run_test(self):
        pass

action_modules: dict[str, Callable[[TestCaseRun, dict, int, dict], int]] = {}


def add_action_module(name: str, action):
    global action_modules
    action_modules[name] = action


def get_all_tests(items: list[str]):
    for it in items:
        for dir_path, dir_names, filenames in os.walk(it):
            for fn in filenames:
                ffn = os.path.join(dir_path, fn)
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
        for testcase in get_all_tests(tests):
            sem_limit.acquire()
            tr = TestCaseRun(tpe, testcase, sem_limit)
            res = tpe.submit(tr.run_testcase)
        for i in range(num_concurrent):
            sem_limit.acquire()
        logging.info('clear for shutdown')
    print('all tests done')
