#!/usr/bin/python3

import argparse
import sys
import flask
import subprocess
import os
import requests
from functools import wraps

HTTP_NOT_FOUND = 404

def signal_send(user, message):
    '''Send message via signal'''
    cmd = [signal_cli_bin, "send", "-m", message, user]
    p = subprocess.run(cmd)

def confirm_dispatch(target, uid):

    '''Confirm to server that message has been dispatched and can be removed'''
    response = requests.post(target + "/confirm-dispatch", json=[{ "uid" : uid }])

    if response.status_code not in [200, 204]:
        print("Failed to confirm disptach with server for {} ({})".format(uid, response.text), file=sys.stderr)


if __name__ == "__main__":

    # set signal cli from env #
    signal_cli_bin = os.environ["SIGNAL_CLI_BIN"]

    parser = argparse.ArgumentParser(description='Query Atlantis Dispatch for Signal',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--target', required=True)
    parser.add_argument('--method', default="signal")
    parser.add_argument('--no-confirm', action="store_true")

    args = parser.parse_args() 


    response = requests.get(args.target + "/get-dispatch?method={}".format(args.method))

    # check status #
    if response.status_code == HTTP_NOT_FOUND:
        sys.exit(0)

    response.raise_for_status()

    for entry in response.json():

        user = entry["person"]
        message = entry["message"]
        uid = entry["uid"]

        # send message #
        if entry["method"] == "signal":
            signal_send(user, message)
        else:
            print("Unsupported dispatch method {}".format(entry["method"]), sys=sys.stderr)
    
        # confirm dispatch
        if not args.no_confirm:
            confirm_dispatch(args.target, uid)

    sys.exit(0)
