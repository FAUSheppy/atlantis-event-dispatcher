import interface
import os
import sys

def createApp(envivorment=None, start_response=None):

    # check files & environment
    signal = os.environ.get("SIGNAL_CLI_BIN")

    if not os.environ.get("SIGNAL_API_PASS"):
        print("SIGNAL_API_PASS must be set in enviromenment", file=sys.stderr)
        sys.exit(1)

    return interface.app
