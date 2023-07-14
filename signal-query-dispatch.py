#!/usr/bin/python3

import argparse
import flask
import subprocess
import os
import requests
from functools import wraps

signal_cli_bin = "signal-cli"

def signal_send(user, message):

    cmd = [signal_send, "send", "-m", message, user]
    p = subprocess.run(cmd)
    p.wait()


def confirm_dispatch(target, uid):

    response = requests.post(target, json=[{ "uid" : uid }])


if __name__ == "__main__":

    signal_cli_bin = os.environ["SIGNAL_CLI_BIN"]

    parser = argparse.ArgumentParser(description='Query Atlantis Dispatch for Signal',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--target', required=True)

    args = parser.parse_args() 

    response = requests.get(args.target)
    HTTP_NOT_FOUND = 404

    # check status #
    if response.status_code == HTTP_NOT_FOUND:
        sys.exit(0)

    response.raise_for_status()

    for entry in response.json():

        user = entry["person"]
        message = entry["message"]

        # send message #
        signal_send(user, message)
    
        # confirm dispatch
        confirm_dispatch(uid) 

    sys.exit(0)
