import interface
import os
import sys

def createApp(envivorment=None, start_response=None):

    # check files & environment
    signal = os.environ.get("SIGNAL_CLI_BIN")
    if not os.environ.get("SIGNAL_API_PASS"):
        print("SIGNAL_API_PASS must be set in enviromenment", file=sys.stderr)
        sys.exit(1)
    elif not os.path.isfile(interface.SIGNAL_USER_FILE):
        print("{} does not exist.".format(interface.SIGNAL_USER_FILE), file=sys.stderr)
        sys.exit(1)
    elif not os.path.getsize(interface.SIGNAL_USER_FILE) > 0:
        print("{} is empty.".format(interface.SIGNAL_USER_FILE), file=sys.stderr)
        sys.exit(1)
    elif not signal or not os.path.isfile(signal):
        print("SIGNAL_CLI_BIN not set or does not exist.", file=sys.stderr)
        sys.exit(1)

    return interface.app
