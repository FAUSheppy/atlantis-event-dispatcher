#!/usr/bin/python3

import argparse
import flask
import sys
import subprocess
import os
import datetime
import secrets

import ldaptools
import messagetools

from sqlalchemy import Column, Integer, String, Boolean, or_, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func


HOST = "icinga.atlantishq.de"
app = flask.Flask("Signal Notification Gateway")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlite.db"
db = SQLAlchemy(app)

class DispatchObject(db.Model):

    __tablename__ = "dispatch_queue"

    username = Column(String, primary_key=True)
    timestamp = Column(Integer, primary_key=True)
    phone = Column(String)
    email = Column(String)
    message = Column(String, primary_key=True)
    method = Column(String)
    dispatch_secret = Column(String)
    dispatch_error = Column(String)

@app.route('/get-dispatch-status')
def get_dispatch_status():
    '''Retrive the status of a specific dispatch by it's secret'''

    secret = flask.request.args.get("secret")
    do = db.session.query(DispatchObject).filter(DispatchObject.dispatch_secret == secret).first()
    if not do:
        return ("Not in Queue",  200)
    else:
        return ("Waiting for dispatch", 200)


@app.route('/get-dispatch')
def get_dispatch():
    '''Retrive consolidated list of dispatched objects'''

    method = flask.request.args.get("method")
    timeout = flask.request.args.get("timeout") or 5 # timeout in seconds

    if not method:
        return (500, "Missing Dispatch Target (signal|email|phone|ntfy|all)")

    # prevent message floods #
    timeout_cutoff = datetime.datetime.now() - datetime.timedelta(seconds=timeout)
    timeout_cutoff_timestamp = timeout_cutoff.timestamp()

    lines_unfiltered = db.session.query(DispatchObject)
    lines_timeout = lines_unfiltered.filter(DispatchObject.timestamp < timeout_cutoff_timestamp)

    if method != "all":
        dispatch_objects = lines_timeout.filter(DispatchObject.method == method).all()
    else:
        dispatch_objects = lines_timeout.all()

    # accumulate messages by person #
    dispatch_by_person = dict()
    dispatch_secrets = []
    for dobj in dispatch_objects:
        if dobj.username not in dispatch_by_person:
            dispatch_by_person.update({ dobj.username : dobj.message })
            dispatch_secrets.append(dobj.dispatch_secret)
        else:
            dispatch_by_person[dobj.username] += "\n{}".format(dobj.message)
            dispatch_secrets.append(dobj.dispatch_secret)

    response = [ { "person" : tupel[0].decode("utf-8"),
                    "message" : tupel[1],
                    "method" : method,
                    "uids" : dispatch_secrets 
                  } for tupel in dispatch_by_person.items() ]

    # add phone numbers and emails #
    for obj in response:
        for person in dispatch_objects:
            if obj["person"] == person.username.decode("utf-8"):
                if person.email:
                    obj.update({ "email" : person.email.decode("utf-8") })
                if person.phone:
                    obj.update({ "phone" : person.phone.decode("utf-8") })

    return flask.jsonify(response)


@app.route('/confirm-dispatch', methods=["POST"])
def confirm_dispatch():
    '''Confirm that a message has been dispatched by replying with its dispatch secret/uid'''

    confirms = flask.request.json

    for c in confirms:

        uid = c["uid"]
        dpo = db.session.query(DispatchObject).filter(DispatchObject.dispatch_secret == uid).first()

        if not dpo:
            return ("No pending dispatch for this UID/Secret", 404)

        db.session.delete(dpo)
        db.session.commit()

    return ("", 204)


@app.route('/smart-send', methods=["POST"])
def smart_send_to_clients():
    '''Send to clients based on querying the LDAP
        requests MAY include:
            - list of usernames under key "users"
            - list of groups    under key "groups"
            - neither of the above to automatically target the configured administrators group"
        retuest MUST include:
            - message as STRING in field "msg"
            OR
            - supported struct of type "ICINGA|ZABBIX|GENERIC" (see docs) in field "data"
    '''

    instructions = flask.request.json

    users = instructions.get("users")
    groups = instructions.get("groups")
    message = instructions.get("msg")

    struct = instructions.get("data")
    if struct:
        try:
            message = messagetools.load_struct(struct)
        except messagetools.UnsupportedStruct as e:
            print(str(e), file=sys.stderr)
            return (e.response(), 408)


    persons = ldaptools.select_targets(users, groups, app.config["LDAP_ARGS"])
    dispatch_secrets = save_in_dispatch_queue(persons, message)
    return flask.jsonify(dispatch_secrets)


def save_in_dispatch_queue(persons, message):


    dispatch_secrets = []
    for p in persons:

        if not p:
            continue

        # this secret will be needed to confirm the message as dispatched #
        dispatch_secret = secrets.token_urlsafe(32)

        obj = DispatchObject(username=p.username,
                        phone=p.phone,
                        email=p.email,
                        method="signal",
                        timestamp=datetime.datetime.now().timestamp(),
                        dispatch_secret=dispatch_secret,
                        message=message)

        db.session.merge(obj)
        db.session.commit()

        dispatch_secrets.append(dispatch_secret)

    return dispatch_secrets

def create_app():

    db.create_all()

    if not app.config.get("LDAP_NO_READ_ENV"):
        ldap_args = {
            "LDAP_SERVER"  : os.environ["LDAP_SERVER"],
            "LDAP_BIND_DN" : os.environ["LDAP_BIND_DN"],
            "LDAP_BIND_PW" : os.environ["LDAP_BIND_PW"],
            "LDAP_BASE_DN" : os.environ["LDAP_BASE_DN"]
        }
        app.config["LDAP_ARGS"] = ldap_args
        print("Setting LDAP_ARGS...")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Simple Telegram Notification Interface',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--interface', default="localhost", help='Interface on which to listen')
    parser.add_argument('--port', default="5000", help='Port on which to listen')
    parser.add_argument("--signal-cli-bin", default=None, type=str,
                            help="Path to signal-cli binary if no in $PATH")

    parser.add_argument('--ldap-server')
    parser.add_argument('--ldap-base-dn')
    parser.add_argument('--ldap-manager-dn')
    parser.add_argument('--ldap-manager-password')

    args = parser.parse_args()

    # define ldap args #
    ldap_args = {
        "LDAP_SERVER" : args.ldap_server,
        "LDAP_BIND_DN" : args.ldap_manager_dn,
        "LDAP_BIND_PW" : args.ldap_manager_password,
        "LDAP_BASE_DN" : args.ldap_base_dn,
    }
    app.config["LDAP_NO_READ_ENV"] = True

    if not any([value is None for value in ldap_args.values()]):
        app.config["LDAP_ARGS"] = ldap_args
    else:
        app.config["LDAP_ARGS"] = None

    with app.app_context():
        create_app()

    app.run(host=args.interface, port=args.port, debug=True)