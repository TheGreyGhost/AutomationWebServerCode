import time

ct_time_debug = False
ct_simulated_time = 0

def current_time():
    """
    returns the current time - can be simulated for debugging
    :return: the current time (unixtime)
    """
    global ct_time_debug
    if not ct_time_debug:
        return time.time()

def simulate_time(newtime):
    """
    sets the simulated time
    :param newtime: the simulated unixtime to use, or None to stop simulation
    :return: N/A
    """
    global ct_time_debug
    global ct_simulated_time
    if newtime is None:
        ct_time_debug = False
        return
    ct_time_debug = True
    ct_simulated_time = newtime
