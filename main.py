"""Main module for the bot.
    Run this module uses webhooks to run the bot and cannot be run in local development.
    Run bot.py to run the bot in local development.
"""

from flask import Flask, request, abort
from bot import bot
from telebot import types

app = Flask(__name__)


@app.route("/")
def main():
    return "<h1>Flask App</h1>"


@app.route("/bot", methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return
    abort(403)
