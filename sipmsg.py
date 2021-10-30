"""
Contains classes for SIP messages
"""

class SipMessage():
    first_line: str
    headers: dict
    body: str
    call_id: str
    cseq: int
