#!/usr/bin/python3

import argparse
import flask
import subprocess
import os

HOST = "icinga.atlantishq.de"
SIGNAL_USER_FILE = "signal_targets.txt"
app = flask.Flask("Signal Notification Gateway")

def dbReadSignalUserFile():
    users = []
    with open(SIGNAL_USER_FILE, "r") as f:
        for line in f:
            user = line.strip()
            if user:
                users.append(user)
    return users

def signalSend(user, msg):
    signalCliBin = "signal-cli"
    if app.config["SIGNAL_CLI_BIN"]:
        signalCliBin = app.config["SIGNAL_CLI_BIN"]
    cmd = [signalCliBin, "send", "-m", msg, user]
    subprocess.Popen(cmd)

def sendMessageToAllClients(msg):
    for number in dbReadSignalUserFile():
        signalSend(number, msg)

@app.route('/send-to-clients', methods=["POST"])
def sendToNumbers():
    for numberOrUser in flask.request.json["users"]:
        signalSend(numberOrUser, flask.request.json["message"])
    return ("","204")

@app.route('/send-all', methods=["POST"])
def sendToAll():
    sendMessageToAllClients(flask.request.json["message"])
    return ("","204")

@app.route('/send-all-grafana', methods=["POST"])
def sendToAllGrafana():
    j = flask.request.json
    state = j["state"]
    if state == "ok":
        string = "Humidity: Ok (<50%)"
    else:
        string = "Humidity: Warning (>50%)"

    sendMessageToAllClients(string)
    return ("","204")

@app.route('/send-all-icinga', methods=["POST"])
def sendToAllIcinga():
    args = flask.request.json

    for key in args.keys():
        if type(args[key]) == str:
            print(key)

    # build message #
    serviceName = args["service_name"]
    if args["service_display_name"]:
        serviceName = args["service_display_name"]

    message = "{service} {state}\n{host}\n{output}".format(service=serviceName,
                                                                state=args["service_state"],
                                                                host=args["service_host"],
                                                                output=args["service_output"])
    sendMessageToAllClients(message)
    return ("","204")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Simple Telegram Notification Interface',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--interface', default="localhost", help='Interface on which to listen')
    parser.add_argument('--port', default="5000", help='Port on which to listen')
    parser.add_argument("--signal-cli-bin", default=None, type=str,
                            help="Path to signal-cli binary if no in $PATH")
    args = parser.parse_args()

    app.config["SIGNAL_CLI_BIN"] = os.path.expanduser(args.signal_cli_bin)

    app.run(host=args.interface, port=args.port)
