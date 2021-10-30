"""
Sip transport layer - very simplified
"""
import logging
import pprint
import socketserver
import threading
import time

import config
import sipmsg

servers = {}
incoming_timeout: float = 0.0

class IncomingSipMsg():
    next: 'IncomingSipMsg'
    signal: threading.Event
    handled=False
    def __init__(self,msg: sipmsg.SipMessage):
        self.signal = threading.Event()
        self.obsolete=time.time()+incoming_timeout
        self.msg=msg

incoming_msgs = IncomingSipMsg(None)
incoming_msgs_lock = threading.Lock()


def add_incoming_msg(msg: sipmsg.SipMessage):
    try:
        incoming_msgs_lock.acquire()
        now=time.time()
        while incoming_msgs.next is not None:
            if incoming_msgs.obsolete < now:
                incoming_msgs=incoming_msgs.next
                continue
            elif incoming_msgs.handled:
                incoming_msgs=incoming_msgs.next
                continue
            else:
                break
        msg=incoming_msgs
        while msg.next is not None:
            if msg.next.handled:
                msg.next=msg.next.next
            else:
                msg=msg.next
        msg.next=IncomingSipMsg(msg)
        msg.signal.set()
    finally:
        incoming_msgs_lock.release()


def all_incoming_msgs():
    """returns all incoming messages as a generator function"""
    msg = incoming_msgs
    while True:
        if not msg.handled and msg.msg is not None:
            yield msg
        if msg.next is None:
            msg.signal.wait()
        msg = msg.next


class SipUdpHandler(socketserver.BaseRequestHandler):
    def handle(self):
        logging.debug('handling a request')


class SipUdpServer():
    remote: (str, int)
    lock = threading.Lock()

    def __init__(self, address):
        logging.info(f'creating UDP server for {address}')
        # needs a class
        self.uds = socketserver.UDPServer(address, SipUdpHandler)
        t = threading.Thread(target=self.uds.serve_forever)
        t.start()

    def shutdown(self):
        self.uds.shutdown()

    def send_msg(self, buffer: bytes):
        try:
            self.lock.acquire()
            self.uds.socket.sendto(buffer, self.remote)
        finally:
            self.lock.release()


def initialize():
    global servers,incoming_timeout
    try:
        logging.debug("initializing sip transport")
        incoming_timeout=config.get_config('incoming_timeout',5.0)
        end_points = config.get_config('endpoints', [])
        pprint.pprint(end_points)
        for ep in end_points:
            name = ep['name']
            eptype = ep['type']
            if eptype == 'sip':
                transport = ep['transport']
                if transport == 'udp':
                    local = ep['local']
                    host = local['host']
                    port = local['port']
                    sus = SipUdpServer((host, port))
                    remote = ep['remote']
                    host = remote['host']
                    port = remote['port']
                    sus.remote = (host, port)
                    servers[name] = sus
                else:
                    s = f'endpoint {name} had unknown transport {transport} '
                    logging.error(s)
                    raise NotImplementedError(s)
            else:
                logging.debug(f'skipped endpoint {name} with type {eptype} ')
    except Exception as ex:
        logging.error(f'initializing sip transport raised exception:\n{ex}')
        raise ex


def shutdown():
    global servers
    try:
        logging.debug('shutting down endpoints')
        for k in servers:
            s = servers[k]
            s.shutdown()
    except Exception as ex:
        logging.error(f'shutting down endpoints got exception {ex}')
        raise ex
