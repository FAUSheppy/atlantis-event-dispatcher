#!/usr/bin/python3

import sys
import time
import argparse
import subprocess
import os
import requests
import smtphelper
import json

HTTP_NOT_FOUND = 404

DISPATCH_SERVER = None
DISPATCH_ACCESS_TOKEN = None

def debug_send(uuid, data, fail_it=False):
    '''Dummy function to print and ack a dispatch for debugging'''

    print(json.dumps(data, indent=2))
    if fail_it:
        report_failed_dispatch(uuid, "Dummy Error for Debugging")
    else:
        confirm_dispatch(uuid)


def email_send(dispatch_uuid, email_address, message, smtp_target,
                smtp_target_port, smtp_user, smtp_pass):
    '''Send message via email'''
  
    if not email_address:
        print("Missing E-Mail Address for STMP send", file=sys.stderr)
        report_failed_dispatch(dispatch_uuid, "Missing email-field in dispatch infor")
        return

    subject = "Atlantis Dispatch"
    smtphelper.smtp_send(smtp_target, smtp_target_port, smtp_user, smtp_pass, email_address,
                            subject, message)
    confirm_dispatch(dispatch_uuid)

def ntfy_api_get_topic(ntfy_api_server, ntfy_api_token, username):
    '''Get the topic of the user'''

    params = {
        "user" : username,
        "token" : ntfy_api_token,
    }

    r = requests.get(ntfy_api_server + "/topic", params=params)
    if r.status_code != 200:
        print(r.text)
        return None
    else:
        print(r.text)
        return r.json().get("topic")

def ntfy_send(dispatch_uuid, user_topic, title, message, ntfy_push_target, ntfy_user, ntfy_pass):
    '''Send message via NTFY topic'''

    if not user_topic:
        report_failed_dispatch(dispatch_uuid, "No user topic")
        return

    try:

        # build message #
        payload = {
            "topic" : user_topic,
            "message" : message,
            "title" : title or "Atlantis Notify",
            #"tags" : [],
            "priority" : 4,
            #"attach" : None,
            "click" : "https://vid.pr0gramm.com/2022/11/06/ed66c8c5a9cd1a3b.mp4",
            #"actions" : []
        }

        # send #
        r = requests.post(ntfy_push_target, auth=(ntfy_user, ntfy_pass), json=payload)
        print(r.status_code, r.text, payload)
        r.raise_for_status()

        # talk to dispatch #
        confirm_dispatch(dispatch_uuid)

    except requests.exceptions.HTTPError as e:
        report_failed_dispatch(dispatch_uuid, str(e))
    except requests.exceptions.ConnectionError as e:
        report_failed_dispatch(dispatch_uuid, str(e))

def report_failed_dispatch(uuid, error):
    '''Inform the server that the dispatch has failed'''

    payload = [{ "uuid" : uuid, "error" : error }]
    response = requests.post(DISPATCH_SERVER + "/report-dispatch-failed", json=payload)

    if response.status_code not in [200, 204]:
        print("Failed to report back failed dispatch for {} ({})".format(
                    uuid, response.text), file=sys.stderr)

def confirm_dispatch(uuid):
    '''Confirm to server that message has been dispatched and can be removed'''

    payload = [{ "uuid" : uuid }]
    response = requests.post(DISPATCH_SERVER + "/confirm-dispatch", json=payload)

    if response.status_code not in [200, 204]:
        print("Failed to confirm dispatch with server for {} ({})".format(
                    uuid, response.text), file=sys.stderr)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Query Atlantis Dispatch for Signal',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--dispatch-server')
    parser.add_argument('--dispatch-access-token')

    parser.add_argument('--ntfy-api-server')
    parser.add_argument('--ntfy-api-token')

    parser.add_argument('--ntfy-push-target')
    parser.add_argument('--ntfy-user')
    parser.add_argument('--ntfy-pass')

    parser.add_argument('--smtp-target')
    parser.add_argument('--smtp-user')
    parser.add_argument('--smtp-pass')
    parser.add_argument('--smtp-port', type=int)

    parser.add_argument('--loop', default=True, action=argparse.BooleanOptionalAction)

    args = parser.parse_args() 


    dispatch_server = args.dispatch_server or os.environ.get("DISPATCH_SERVER")
    dispatch_access_token = args.dispatch_access_token or os.environ.get("DISPATCH_ACCESS_TOKEN")

    # set dispatch server & authentication global #
    DISPATCH_SERVER = dispatch_server
    DISPATCH_ACCESS_TOKEN = dispatch_access_token

    ntfy_api_server = args.ntfy_api_server or os.environ.get("NTFY_API_SERVER")
    ntfy_api_token = args.ntfy_api_token or os.environ.get("NTFY_API_TOKEN")

    ntfy_push_target = args.ntfy_push_target or os.environ.get("NTFY_PUSH_TARGET")
    ntfy_user = args.ntfy_user or os.environ.get("NTFY_USER")
    ntfy_pass = args.ntfy_pass or os.environ.get("NTFY_PASS")

    smtp_target = args.smtp_target or os.environ.get("SMTP_TARGET")
    smtp_user = args.smtp_user or os.environ.get("SMTP_USER")
    smtp_pass = args.smtp_pass or os.environ.get("SMTP_PASS")
    smtp_port = args.smtp_port or os.environ.get("SMTP_PORT")

    first_run = True
    while args.loop or first_run:

        # request dispatches #
        response = requests.get(dispatch_server + 
            "/get-dispatch?method=all&timeout=0&dispatch-access-token={}".format(DISPATCH_ACCESS_TOKEN))

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

            user = entry["username"]
            dispatch_uuid = entry["uuid"]
            method = entry["method"]
            message = entry["message"]
            title = entry.get("title")

            # method dependent fields #
            phone = entry.get("phone")
            email_address = entry.get("email")

            # send message #
            if method == "signal":
                pass
            elif method == "ntfy":
                user_topic = ntfy_api_get_topic(ntfy_api_server, ntfy_api_token, user)
                ntfy_send(dispatch_uuid, user_topic, title, message,
                                ntfy_push_target, ntfy_user, ntfy_pass)
            elif method == "email":
                email_send(dispatch_uuid, email_address, message, smtp_target,
                                smtp_port, smtp_user, smtp_pass)
            elif method == "debug":
                debug_send(dispatch_uuid, entry)
            elif method == "debug-fail":
                debug_send(dispatch_uuid, entry, fail_it=True)
            else:
                print("Unsupported dispatch method {}".format(entry["method"]), sys=sys.stderr)
                continue

        # wait a moment #
        if args.loop:
            time.sleep(5)
        
        # handle non-loop runs #
        first_run = False
