"""
Contains classes for SIP messages
"""
import logging


class SipMessage:
    """
    full sip message decomposed into components
    """
    firstline: str=''
    """the first line of request or response"""
    # headers can be repeated, VIA, Record-Route, Route
    headers: dict[str, list[str]]={}
    """"all headers"""
    # body as one single string, since there is no manipulation in here
    body: str=''
    # storing special elements separate after parsing
    call_id: str=''
    cseq: int=0

    def __init__(self, fl: str, hdrs: str, body: str):
        """
        build a SIP-message from it's main component, also extracts special elements
        """
        logging.debug("constructing sipmessage from parts")
        if body is None:
            self.body = ''
        else:
            body = "\r\n".join(body.splitlines()) + "\r\n"
            self.body = body
        for hdr in hdrs.splitlines():
            hdr = hdr.strip()
            if len(hdr) == 0:
                continue
            hdr = hdr.split(':', 1)
            if not hdr[0] in self.headers:
                self.headers[hdr[0]] = []
            self.headers[hdr[0]].append(hdr[1])
        self.firstline = fl.strip()
        # TODO call_id, cseq

    def __init__(self, msg: str):
        """analyzes msg and extracts the parts"""
        logging.debug("constructing sipmessage from message")
