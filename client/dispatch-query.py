#!/usr/bin/python3

import sys
import subprocess
import os
import requests
from functools import wraps

HTTP_NOT_FOUND = 404
AUTH = None

def email_address(dispatch_uuid, user_topic, message, smtp_target, smtp_user, smtp_pass):
    '''Send message via email'''

    report_failed_dispatch(uuid, "Email dispatch not yet implemented")

def ntfy_send(dispatch_uuid, user_topic, message, ntfy_push_target, ntfy_user, ntfy_pass):
    '''Send message via NTFY topic'''

    try:
        r = requests.post(ntfy_push_target, auth=(ntfy_user, ntfy_pass) , json=payload)
        r.raise_for_status()
        confirm_dispatch(uuid)
    except requests.exceptions.HTTPError as e:
        report_failed_dispatch(uuid, str(e))
    except requests.exceptions.ConnectionError as e:
        report_failed_dispatch(uuid, str(e))

def report_failed_dispatch(uuid, error):
    '''Inform the server that the dispatch has failed'''

    response = requests.post(args.dispatch_target + "/report-dispatch-failed",
                                json={ "uuid" : uuid, "error" : error })

    if response.status_code not in [200, 204]:
        print("Failed to report back failed dispatch for {} ({})".format(
                    uuid, response.text), file=sys.stderr)

def confirm_dispatch(uuid):
    '''Confirm to server that message has been dispatched and can be removed'''

    response = requests.post(target + "/confirm-dispatch", json=[{ "uuid" : uuid }],
                                auth=(args.user, args.password))

    if response.status_code not in [200, 204]:
        print("Failed to confirm dispatch with server for {} ({})".format(
                    uuid, response.text), file=sys.stderr)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Query Atlantis Dispatch for Signal',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--dispatch-server')
    parser.add_argument('--dispatch-user')
    parser.add_argument('--dispatch-password')

    parser.add_argument('--ntfy-push-target')
    parser.add_argument('--ntfy-user')
    parser.add_argument('--ntfy-pass')

    parser.add_argument('--smtp-target')
    parser.add_argument('--smtp-user')
    parser.add_argument('--smtp-pass')

    args = parser.parse_args() 

    # set authentication #
    AUTH = (args.dispatch_user, args.dispatch_password)

    dispatch_server = args.dispatch_server or os.environ.get("DISPATCH_SERVER")
    dispatch_user = args.dispatch_user or os.environ.get("DISPATCH_USER")
    dispatch_password = args.dispatch_password or os.environ.get("DISPATCH_PASSWORD")

    ntfy_push_target = args.ntfy_push_target or os.environ.get("NTFY_PUSH_TARGET")
    ntfy_user = args.ntfy_user or os.environ.get("NTFY_USER")
    ntfy_pass = args.ntfy_pass or os.environ.get("NTFY_PASS")

    smtp_target = args.smtp_target or os.environ.get("SMTP_TARGET")
    smtp_user = args.smtp_user or os.environ.get("SMTP_USER")
    smtp_pass = args.smtp_pass or os.environ.get("SMTP_PASS")

    # request dispatches #
    response = requests.get(args.target + "/get-dispatch".format(args.method),
                            auth=(args.user, args.password))

    # check status #
    if response.status_code == HTTP_NOT_FOUND:
        sys.exit(0)

    # fallback check for status #
    response.raise_for_status()

    # track dispatches that were confirmed to avoid duplicate confirmation #
    dispatch_confirmed = []

    # track failed dispatches #
    errors = dict()

    # iterate over dispatch requests #
    for entry in response.json():

        user = entry["person"]
        dispatch_uuid = entry["uid"]
        method = entry["method"]
        message = entry["message"]

        # method dependent fields #
        user_topic = entry.get("topic")
        phone = entry.get("phone")
        email_address = entry.get("email")

        # send message #
        if method == "signal":
            pass
        elif method == "ntfy":
            ntfy_send(dispatch_uuid, user_topic, message, ntfy_push_target, ntfy_user, ntfy_pass)
        elif method == "email":
            email_send(email_address, message)
        else:
            print("Unsupported dispatch method {}".format(entry["method"]), sys=sys.stderr)
            continue

    sys.exit(0)
