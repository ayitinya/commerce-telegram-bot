"""Main module for the bot.
    Run this module uses webhooks to run the bot and cannot be run in local development.
    Run bot.py to run the bot in local development.
"""

# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`


from firebase_functions import https_fn
from firebase_functions.firestore_fn import (
    on_document_created,
    on_document_updated,
    Change,
    Event,
    DocumentSnapshot,
)

import firebase_admin

import sentry_sdk
from flask import Flask, request, abort
from telebot import types

from bot import bot, db

import config
from data.DatabaseInterface import Order, OrderItem, User
from data.firestore import not_none

try:
    firebase_admin.initialize_app()
except ValueError:
    pass


sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    debug=config.ENV == "development",
    environment=config.ENV,
    project_root=config.ROOT_DIR,
    attach_stacktrace=True,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


app = Flask(__name__)


@app.route("/")
def main():
    """
    Default route for the Flask app.
    Returns a simple HTML response.
    """
    return "<h1>Flask App</h1>"


@app.route("/test-sentry")
def hello_world():
    """
    This function will raise an exception and sentry will capture.
    """
    print(f"{1/0}")  # raises an exception
    return "<p>Use Sentry, it can save your life!</p>"


@app.route("/bot", methods=['POST'])
def webhook():
    """
    Webhook endpoint for receiving updates from Telegram.
    Processes the updates using the bot module.
    """
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = types.Update.de_json(json_string)
        if update:
            try:
                bot.process_new_updates([update])
            except Exception as e:  # pylint: disable=broad-except
                sentry_sdk.capture_exception(e)
                return "Success", 200, {"Access-Control-Allow-Origin": "*"}

        return "Success", 200, {"Access-Control-Allow-Origin": "*"}
    abort(403)


@https_fn.on_request()
def expose_flask_server(req: https_fn.Request) -> https_fn.Response:
    """
    Cloud Function endpoint for exposing the Flask server.
    """
    with app.request_context(req.environ):
        return app.full_dispatch_request()


@on_document_created(document="orders/{order_id}")
def order_created(event: Event) -> None:
    """
    Cloud Function endpoint for handling order creation.
    """
    order: DocumentSnapshot = event.data

    order_processed = Order(**not_none(order.to_dict()))
    admins = db.get_admins()
    for admin in admins:
        bot.send_message(
            admin.id_,
            f"""Order created! Please contact the user to confirm the order.
            
            User ID: {order_processed.user.id_}
            Name: {order_processed.user.display_name}
            
            Order ID: {order_processed.id_}
            Items: {order_processed.items}
            
            For more information, vistit the web portal
            
            """,
        )


@on_document_updated(document="orders/{order_id}")
def order_updated(event: Event) -> None:
    """
    Cloud Function endpoint for handling order updates.
    """
    change: Change = event.data
    order: DocumentSnapshot = change.after

    order_processed = Order(user=User(**order.get("user")), id_=order.id, total_cost=order.get(
        "total_cost"), items=[OrderItem(**order_item) for order_item in order.get("items")], state=order.get("state"))

    bot.send_message(
        order_processed.user.id_,
        f"""Your order has been updated.
        
        Order ID: {order_processed.id_}
        state: {order_processed.state}
        """,
    )
