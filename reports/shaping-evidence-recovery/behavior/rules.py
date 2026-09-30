ALLOWED_STATES = {"ready"}

def eligible(state):
    return state in ALLOWED_STATES
