# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import machine
rst_cause = machine.reset_cause()
if rst_cause == machine.HARD_RESET:
    print("Hard Reset")
elif rst_cause == machine.SOFT_RESET:
    print("Soft Reset")
elif rst_cause == machine.WDT_RESET:
    print("WDT Reset")


import json

import nextion
from thermostat import Thermostat

driver = nextion.Driver()

with open("nextion.json", "r") as fp:
    data = json.loads(fp.read())

driver.pages = [nextion.Page.new_page_by_specification(driver, s) for s in data]