""""
Testing infrastructure

"""
import concurrent.futures.thread
import logging
import os
import pprint
import threading
from datetime import datetime
from typing import Callable, TextIO

import yaml
import config


class TestCaseRun:
    """
    infrastructure to run a testcase contain one or more threads
    """
    running: bool
    data = {}

    def __init__(self, tpe: concurrent.futures.thread.ThreadPoolExecutor, testcase: dict, sem: threading.Semaphore):
        self.running = True
        """stop all loops when test case is no longer running"""
        self.tpe = tpe
        """use this ThreadPoolExecutor for threads"""
        self.data = testcase
        """Test case to try"""
        self.sem = sem
        """when test case is done, release this semaphore 
            - it is used to limit the number of concurrent test case executions"""

    def run_testcase(self):
        """Runs a single testcase"""
        try:
            tn = 'test-not-named'
            if 'name' in self.data:
                tn = self.data['name']
            else:
                self.data['name'] = tn
            fn = self.data['filename']
            future_threads = []
            logging.info(f'running test {fn} -> {tn}')
            pp = os.path.join('logs', fn)
            os.makedirs(pp, exist_ok=True)
            # don't need to save this logger
            logf = open(os.path.join(pp, tn + '.txt'), 'wt')
            now = datetime.now().strftime('%Y-%m-%d %X')
            print(f'tested at {now}', file=logf)
            if 'threads' not in self.data or not isinstance(self.data['threads'], list):
                logging.error(f' no defined threads (must be a list of actions) in {fn}->{tn}')
                return
            for t in self.data['threads']:
                # new structure for each thread
                ttr = TestThreadRun(self, t)
                res = self.tpe.submit(ttr.run_test)
                future_threads.append(res)
            # test is first done when all test threads are finished
            concurrent.futures.wait(future_threads)
        except Exception as ex:
            logging.error(f' got an exception {ex}')
        finally:
            self.sem.release()
            if logf is not None:
                logf.close()

    def run_thread(self, t):
        """
        obsolete
        """
        global action_modules
        logging.error("should not be called")
        try:
            tn = self.data['name']
            fn = self.data['filename']
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
    logf: TextIO = None
    data = {}
    action: int = 0

    def __init__(self, tc: TestCaseRun, t: dict):
        self.parent = tc
        self.data.update(tc.data)
        self.data['thread'] = t

    def run_test(self):
        try:
            tn = 'unnamed'
            if 'name' in self.data:
                tn = self.data['name']
            fn = self.data['filename']
            trn = 'unnamed'
            if 'name' in self.data['thread']:
                trn = self.data['thread']['name']
            logging.info(f'running thread {trn} for {fn}->{tn}')
            pp = os.path.join('logs', fn, tn)
            os.makedirs(pp, exist_ok=True)
            self.logf = open(os.path.join(pp, trn + ".txt"), 'wt')
            actions = self.data['thread']['actions']
            action_count = len(actions)
            while self.parent.running:
                if self.action >= action_count:
                    break
                action_data = actions[self.action]
                self.data['step'] = action_data
                action_name = action_data['action']
                if action_name not in action_modules:
                    s = f'action "{action_name}" is not implemented'
                    logging.error(s)
                    print(s, file=self.logf)
                    raise NotImplementedError(s)
                action_modules[action_name](self)
        except Exception as ex:
            logging.error(f"got an exception {ex}")
        finally:
            if self.logf is not None:
                self.logf.close()
        logging.error("more implementation to be done")
        pass


action_modules: dict[str, Callable[[TestThreadRun], None]] = {}


def add_action_module(name: str, action: Callable[[TestThreadRun], None]):
    """
    adds one action to the dictionary,
    called by the initialize function of the action modules
    """
    global action_modules
    action_modules[name] = action


def get_all_tests(items: list[str]):
    # generator function that returns all test cases read from the respective yaml files
    # this function ends when all items are read
    for it in items:
        for dir_path, dir_names, filenames in os.walk(it):
            for fn in filenames:
                # preparing to read the content
                ffn = os.path.join(dir_path, fn)
                with open(ffn) as inp:
                    tt = yaml.safe_load(inp)
                    # can be single test or list of tests
                    if isinstance(tt, list):
                        for t in tt:
                            # safeguard against format errors
                            if not isinstance(t, dict):
                                t_str = pprint.pformat(t)
                                logging.error(f'file {ffn} contains an error with {t_str}')
                                continue
                            t['filename'] = ffn
                            yield t
                    else:
                        # safeguard against format errors
                        if not isinstance(tt, dict):
                            t_str = pprint.pformat(t)
                            logging.error(f'file {ffn} contains an error with {t_str}')
                            continue
                        tt['filename'] = ffn
                        yield tt


def run_tests(tests: list[str]):
    """
    main test function with a list of files/directories as argument
    """
    logging.debug("running tests")
    num_concurrent = config.get_config('concurrent', 1)
    # sem_limit restricts the number of concurrent test executions
    sem_limit = threading.Semaphore(num_concurrent)
    # a TPE keeps threads for the next task
    with concurrent.futures.ThreadPoolExecutor() as tpe:
        for testcase in get_all_tests(tests):
            # wait for it's turn
            sem_limit.acquire()
            # creating test case runner
            tr = TestCaseRun(tpe, testcase, sem_limit)
            res = tpe.submit(tr.run_testcase)
        # all tests are submitted, need to wait for all to finish
        for i in range(num_concurrent):
            sem_limit.acquire()
        logging.info('clear for shutdown')
    # TPE shuts down, waits for all threads to finish
    print('all tests done')
