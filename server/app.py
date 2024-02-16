import interface as main
import os
import sys

def createApp(envivorment=None, start_response=None):
    with main.app.app_context():
        main.create_app()
    return main.app
