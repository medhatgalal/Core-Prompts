ALLOWED_STATES = {"ready"}

def eligible(state):
    return state in ALLOWED_STATES

def route(state):
    return eligible(state)

def sample():
    return route("ready")

def test_route():
    assert route("ready") is True
    assert route("paused") is False
