#!/usr/bin/python3

import argparse
import sys
import flask
import subprocess
import os
import requests
from functools import wraps

HTTP_NOT_FOUND = 404

def signal_send(phone, message):
    '''Send message via signal'''
    cmd = [signal_cli_bin, "send", "-m", "'{}'".format(message.replace("'","")), phone]
    p = subprocess.run(cmd)

def confirm_dispatch(target, uid):

    '''Confirm to server that message has been dispatched and can be removed'''
    response = requests.post(target + "/confirm-dispatch", json=[{ "uid" : uid }],
                                auth=(args.user, args.password))

    if response.status_code not in [200, 204]:
        print("Failed to confirm disptach with server for {} ({})".format(uid, response.text), file=sys.stderr)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Query Atlantis Dispatch for Signal',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--target', required=True)
    parser.add_argument('--method', default="signal")
    parser.add_argument('--no-confirm', action="store_true")
    parser.add_argument('--signal-cli-bin')

    parser.add_argument('--user')
    parser.add_argument('--password')

    args = parser.parse_args() 

    if args.signal_cli_bin:
        signal_cli_bin = args.signal_cli_bin

    response = requests.get(args.target + "/get-dispatch?method={}".format(args.method),
                            auth=(args.user, args.password))

    # check status #
    if response.status_code == HTTP_NOT_FOUND:
        sys.exit(0)

    response.raise_for_status()

    dispatch_confirmed = []
    for entry in response.json():

        user = entry["person"]
        phone = entry["phone"]
        message = entry["message"]
        uid_list = entry["uids"]

        # send message #
        if entry["method"] == "signal":
            signal_send(phone, message)
        else:
            print("Unsupported dispatch method {}".format(entry["method"]), sys=sys.stderr)
    
        # confirm dispatch
        if not args.no_confirm:
            for uid in uid_list:
                if uid not in dispatch_confirmed:
                    confirm_dispatch(args.target, uid)
                    dispatch_confirmed.append(uid)
                else:
                    continue

    sys.exit(0)
