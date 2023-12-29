"""Main module for the bot.
    Run this module uses webhooks to run the bot and cannot be run in local development.
    Run bot.py to run the bot in local development.
"""

# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app

from flask import Flask, request, abort
from bot import bot
from telebot import types

initialize_app()
#
#
# @https_fn.on_request()
# def on_request_example(req: https_fn.Request) -> https_fn.Response:
#     return https_fn.Response("Hello world!")



app = Flask(__name__)


@app.route("/")
def main():
    return "<h1>Flask App</h1>"


@app.route("/bot", methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        if update:
            bot.process_new_updates([update])
        return "working"
    abort(403)
    
    

@https_fn.on_request()
def expose_flask_server(req: https_fn.Request) -> https_fn.Response:
    with app.request_context(req.environ):
        return app.full_dispatch_request()