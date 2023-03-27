from dataclasses import dataclass


@dataclass
class State:
    force: bool = False
    token: str = "no-token"
    dmss_url: str = "http://localhost:5000"
    debug: bool = False


state = State()
