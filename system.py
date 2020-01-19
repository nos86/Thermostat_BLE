import machine # pylint: disable=import-error

global wlan0
wlan0 = None

global reset_cause
reset_cause = None

def print_reset_cause():
    if reset_cause == machine.HARD_RESET:
        print("Hard Reset")
    elif reset_cause == machine.SOFT_RESET:
        print("Soft Reset")
    elif reset_cause == machine.WDT_RESET:
        print("WDT Reset")