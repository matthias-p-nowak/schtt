"""
Contains classes for SIP messages
"""
import logging


class SipMessage:
    firstline: str=''
    headers: dict[str, list[str]]={}
    body: str=''
    call_id: str=''
    cseq: int=0

    def __init__(self, fl: str, hdrs: str, body: str):
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

    def __int__(self, msg: str):
        logging.debug("constructing sipmessage from message")
