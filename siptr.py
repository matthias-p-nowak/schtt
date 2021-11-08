"""
Sip transport layer - very simplified
Incoming messages are stored in a linked list for each thread to scan
incoming messages are synchronized and already handled or obsolete messages are removed from the list.
"""
import logging
import pprint
import socketserver
import threading
import time
from threading import Lock

import config
import sipmsg

servers = {}
incoming_timeout: float = 0.0


class IncomingSipMsg():
    """storing incoming messages in a linked list"""
    next: 'IncomingSipMsg'
    """the next incoming message"""
    signal: threading.Event
    """signal fired after the next message is adding in next"""
    handled: bool
    """true if some thread has already handled this message"""

    def __init__(self, msg: sipmsg.SipMessage, handled=False):
        self.signal = threading.Event()
        # store when this message should be at the latest removed
        self.obsolete = time.time() + incoming_timeout
        self.msg = msg
        self.handled = handled


incoming_msgs = IncomingSipMsg(None, handled=True)
"""starting point for the linked list"""
incoming_msgs_lock: Lock = threading.Lock()
"""lock for synchronizing additions to the """


def log_unhandled_msg(msg: sipmsg.SipMessage):
    # TODO printout unhandled message
    pass


def add_incoming_msg(msg: IncomingSipMsg):
    """
    adds a new message to the list
    before adding, it removes old handled/obsolete
    """
    global incoming_msgs, incoming_msgs_lock
    try:
        # serializing access to the linked list
        incoming_msgs_lock.acquire()
        now = time.time()
        # keep at least one element in the list - and check the first element
        while incoming_msgs.next is not None:
            if incoming_msgs.obsolete < now:
                # first message is obsolete, move the starting pointer
                log_unhandled_msg(incoming_msgs)
                incoming_msgs = incoming_msgs.next
                continue
            elif incoming_msgs.handled:
                # first message was already handled
                incoming_msgs = incoming_msgs.next
                continue
            else:
                break
        # starting pointer moved as far as possible,
        # no removal of elements within the list
        msg = incoming_msgs
        while msg.next is not None:
            if msg.next.handled:
                msg.next = msg.next.next
            elif msg.obsolete < now:
                log_unhandled_msg(msg)
                msg.next = msg.next.next
            else:
                msg = msg.next
        # First, add the next message
        msg.next = IncomingSipMsg(msg)
        # then fire signal/event, so waiting threads can continue
        msg.signal.set()
    finally:
        incoming_msgs_lock.release()


def all_incoming_msgs():
    """
    returns all incoming messages as a generator function
    blocks when there are no further messages
    """
    msg = incoming_msgs
    # never ending generator, caller ends this loop
    while True:
        if not msg.handled:
            yield msg
        if msg.next is None:
            msg.signal.wait()
        msg = msg.next


class SipUdpHandler(socketserver.BaseRequestHandler):
    """
    each incoming SIP message creates a new instance of this class
    """
    def handle(self):
        logging.debug(f"handling a request")
        # TODO handle a request - aka reading from socket
        logging.debug(f"got {pprint.pformat(self.request)}")
        # TODO add the message to the incoming list


class SipUdpServer:
    """
    UDP Server part
    """
    remote_side: (str, int)
    """remote side"""
    write_lock = threading.Lock()

    def __init__(self, local_side: (str, int), remote_side: (str, int)):
        """
        creates an UDP endpoints and starts server thread
        """
        self.remote_side=remote_side
        logging.info(f"creating UDP server for {local_side}")
        # needs a class to register as the receptacle of the message
        self.uds = socketserver.UDPServer(local_side, SipUdpHandler)
        # the serve_forever reads all incoming messages
        t = threading.Thread(target=self.uds.serve_forever)
        # thread ends with shutdown
        t.start()

    def shutdown(self):
        """closes the socket"""
        self.uds.shutdown()

    def send_msg(self, buffer: bytes):
        """synchronized sending of messages on that buffer"""
        try:
            self.write_lock.acquire()
            self.uds.socket.sendto(buffer, self.remote_side)
        finally:
            self.write_lock.release()


def initialize():
    """
    creates remote endpoints
    """
    global servers, incoming_timeout
    try:
        logging.debug("initializing sip transport")
        incoming_timeout = config.get_config('incoming_timeout', 5.0)
        # endpoints contains the necessary connections
        end_points = config.get_config('endpoints', [])
        pprint.pprint(end_points)
        for name in end_points:
            ep = end_points[name]
            ep_type = ep['type']
            # doing sip endpoints
            if ep_type == 'sip':
                transport = ep['transport']
                if transport == 'udp':
                    local = ep['local']
                    remote = ep['remote']
                    local_side=(local['host'],local['port'])
                    remote_side=(remote['host'],remote['port'])
                    sus = SipUdpServer(local_side,remote_side)
                    # register connection
                    servers[name] = sus
                # TODO add tcp part
                else:
                    s = f"endpoint {name} had unknown transport {transport} "
                    logging.error(s)
                    raise NotImplementedError(s)
            else:
                logging.debug(f"skipped endpoint {name} with type {ep_type} ")
    except Exception as ex:
        logging.error(f"initializing sip transport raised exception:\n{ex}")
        raise ex


def shutdown():
    """
    shutting down all installed connections
    """
    global servers
    try:
        logging.debug("shutting down endpoints")
        for k in servers:
            s = servers[k]
            s.shutdown()
    except Exception as ex:
        logging.error(f"shutting down endpoints got exception {ex}")
        raise ex
