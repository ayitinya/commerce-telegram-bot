""" This is the main file for the bot 
    Run this file to start the bot when in development
"""

import decimal
import logging

import telebot

import config
import media_handler
from db import DB

db = DB(echo=False)
db.create()

bot = telebot.TeleBot(config.API_KEY, threaded=False)  # free pythonanywhere hosting doesn't support threading

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

step = {}
new_product = {}
orders_in_progress = {}


def modify_step(chat_id, new_step, reset=False):
    chat_id = str(chat_id)

    if chat_id not in step:
        step[chat_id] = {"current": "", "path": []}

    if reset:
        step[chat_id] = {"current": "", "path": []}
        step[chat_id]["path"].append(new_step)
        step[chat_id]["current"] = new_step
        return

    step[chat_id]["current"] = new_step
    step[chat_id]["path"].append(new_step)


def display_main_menu(chat_id, text):
    menu_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=2)

    menu_markup.row("Make A Purchase")
    menu_markup.add("View Cart", "Checkout")

    modify_step(chat_id, "start", reset=True)

    bot.send_message(chat_id=chat_id, text=text, reply_markup=menu_markup)


def display_products(chat_id):
    products_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select A Product", row_width=2)

    product_list = db.get_products()
    products_markup.add(*product_list)

    products_markup.row("Checkout", "View Cart")
    products_markup.row("Main Menu")

    text = "Hello, what would you like to purchase?\nSelect a product from the list below"

    modify_step(chat_id, "display_products")

    bot.send_message(chat_id=chat_id, text=text, reply_markup=products_markup)


def display_cart(chat_id, ):
    cart = db.get_cart(chat_id)

    if not cart['products']:
        text = "Your cart is empty"
        bot.send_message(chat_id=chat_id, text=text)
        return

    text = f"Total Cost: {cart['total_cost']}\n\n"
    for product in cart["products"]:
        text += f"Product: {product['product']}\nQuantity: {product['quantity']}\n\n"

    bot.send_message(chat_id=int(chat_id), text=text)


@bot.message_handler(commands=['start'])
def start_handler(message):
    if db.get_user(message.chat.id) is None:
        fullname = f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
        db.new_user(message.chat.id, fullname=fullname)

    text = f"Hello {message.from_user.first_name}, welcome to our store.\n\nWhat would you like to do?"

    display_main_menu(message.chat.id, text)


@bot.message_handler(commands=['cancel'])
def cancel_handler(message):
    user = db.get_user(message.chat.id)
    if user and user.is_admin:
        display_admin_menu(message.chat.id, "What would you like to do next?")
        return
    display_main_menu(message.chat.id, "What would you like to do next?")


@bot.message_handler(commands=['admin'])
def admin_handler(message):
    if db.get_user(message.chat.id) is None:
        fullname = f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
        db.new_user(message.chat.id, fullname=fullname)

    text = "Welcome Admin, enter the password to continue"
    modify_step(message.chat.id, "admin_password", reset=True)
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda message: message.text == "Make A Purchase")
def make_purchase_handler(message):
    modify_step(message.chat.id, "make_purchase")
    display_products(message.chat.id)


@bot.message_handler(func=lambda message: message.text in ("Checkout", "Proceed To Checkout"))
def checkout_handler(message):
    modify_step(message.chat.id, "checkout")
    cart = db.get_cart(message.chat.id)

    if not cart['products']:
        text = "Your cart is empty"
        display_main_menu(message.chat.id, text)
        return
    user = db.get_user(message.chat.id)

    text = "Please enter your phone number to proceed with payment\n\nFormat: 0201234567"
    modify_step(message.chat.id, "phone_number")

    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Enter Phone Number")

    if user.phone:
        reply_markup.add(user.phone)
    reply_markup.add("Main Menu")
    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(func=lambda message: message.text == "View Cart")
def view_cart_handler(message):
    modify_step(message.chat.id, "view_cart")

    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=1)
    reply_markup.add("Main Menu")

    reply_markup.add("Proceed To Checkout")
    display_cart(message.chat.id)
    display_main_menu(message.chat.id, "What would you like to do next?")


@bot.message_handler(func=lambda message: message.text == "Main Menu")
def main_menu_handler(message):
    display_main_menu(message.chat.id, "What would you like to do next?")


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "display_products")
def product_selection_handler(message):
    import requests

    products = db.get_products()
    reply = f"Product: {message.text}\nPrice: {products[message.text]['price']}\n\nHow many would you like to purchase?"
    image = requests.get(products[message.text]["image"]).content

    quantity_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Enter Quantity", row_width=3)
    quantity_markup.add(*[str(i) for i in range(1, 11)], "Back")

    modify_step(message.chat.id, "product_selection")

    orders_in_progress[str(message.chat.id)] = {
        "product": message.text,
        "price": products[message.text]["price"],
        "quantity": 0
    }
    bot.send_photo(message.chat.id, image, caption=reply,
                   reply_markup=quantity_markup)


@bot.message_handler(
    func=lambda message: message.text.isdecimal() and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "product_selection")
def quantity_selection_handler(message):
    modify_step(message.chat.id, "quantity_selection")

    chat_id = str(message.chat.id)
    orders_in_progress[chat_id]["quantity"] = int(message.text)
    product = orders_in_progress[chat_id]["product"]
    product_price = orders_in_progress[chat_id]["price"]
    total_cost = int(message.text) * decimal.Decimal(product_price)

    text = f"{product}\nQuantity: {message.text}\nTotal Cost: {total_cost}\n\nWould you like to add this to your cart?"

    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option")
    reply_markup.row("Yes", "No")
    reply_markup.row("Back")

    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(func=lambda message: message.text == "Yes" or message.text == "No" and step[str(message.chat.id)][
    "current"] == "quantity_selection")
def add_to_cart_handler(message):
    chat_id = str(message.chat.id)

    if message.text == "Yes":
        if chat_id not in orders_in_progress:
            bot.send_message(chat_id=message.chat.id, text="An error occurred, please try again")
            display_main_menu(
                message.chat.id, "What would you like to do next?")
            return

        db.add_to_cart(chat_id, orders_in_progress[chat_id]["product"],
                       orders_in_progress[chat_id]["quantity"], orders_in_progress[chat_id]["price"])

        text = "Product added to cart"

    else:
        text = "Product not added to cart"

    orders_in_progress[chat_id] = None

    modify_step(message.chat.id, "add_to_cart")

    bot.send_message(chat_id=message.chat.id, text=text)
    display_main_menu(
        message.chat.id, text="What would you like to do next?\nSelect checkout to proceed with payment")


@bot.message_handler(
    func=lambda message: message.text == "Back" and step[str(message.chat.id)]["current"] == "product_selection")
def quantity_selection_back_handler(message):
    orders_in_progress[str(message.chat.id)] = None
    display_products(message.chat.id)


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "phone_number")
def phone_number_handler(message):
    chat_id = str(message.chat.id)
    phone = message.text

    if len(phone) != 10 or not phone.isdecimal():
        text = "Please enter a valid phone number\n\nFormat: 0201234567"
        bot.send_message(chat_id=message.chat.id, text=text)
        return

    user = db.update_user(chat_id, phone=phone)

    modify_step(message.chat.id, "address")
    text = "Please enter your address\n\nFormat: 1234 Street Name, City, Region\n\nExample: 1234 Street Name, Accra, Greater Accra"
    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option")
    reply_markup.row(user.address)
    reply_markup.row("Main Menu")
    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "address")
def address_handler(message):
    chat_id = str(message.chat.id)
    address = message.text

    user = db.update_user(chat_id, address=address)

    modify_step(message.chat.id, "name")
    text = "Please enter your name\n\nFormat: First Name Last Name\n\nExample: John Doe"
    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option")
    reply_markup.row(user.fullname)
    reply_markup.row("Main Menu")
    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "name")
def name_handler(message):
    chat_id = str(message.chat.id)
    name = message.text

    user = db.update_user(chat_id, fullname=name)

    modify_step(message.chat.id, "confirm_order")

    text = "Your order of"
    bot.send_message(chat_id=message.chat.id, text=text)
    display_cart(message.chat.id)
    text = f"will be delivered to\n\n{user.fullname}\n\n{user.address}\n\n{user.phone}\n\nPlease confirm your order"
    bot.send_message(chat_id=message.chat.id, text=text)
    text = "Due to current limitations, we only accept cash payments." \
           "Once you confirm your order, you will be contacted by our delivery agent to arrange payment and delivery."

    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select Payment Method", row_width=1)
    reply_markup.add("Cancel Order")
    reply_markup.add("Proceed")

    modify_step(message.chat.id, "confirm_order")
    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


def alert_admins_of_new_order(order_id):
    order = db.get_order(order_id)
    text = f"New order from {order['fullname']}\n\nAddress: {order['address']}\n\nPhone:{order['phone']}\n\nOrder ID: {order_id}\n\nOrder Details:\n\n"
    text += "\n".join([f"{item['product']} - {item['quantity']} - GHC {item['price']}" for item in order['items']])
    text += f"\n\nTotal: GHC {order['total_cost']}"

    reply_markup = telebot.types.InlineKeyboardMarkup()
    reply_markup.add(telebot.types.InlineKeyboardButton("Cancel Order", callback_data=str(
        {"action": "Cancel Order", "order_id": order_id})))
    reply_markup.add(telebot.types.InlineKeyboardButton("Confirm Order", callback_data=str(
        {"action": "Confirm Order", "order_id": order_id})))
    users_to_alert = db.get_notification_users()
    for user in users_to_alert:
        bot.send_message(chat_id=user, text=text, reply_markup=reply_markup)


@bot.message_handler(
    func=lambda message: message.text == "Proceed" and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "confirm_order")
def confirm_order_handler(message):
    text = "Your order is being processed. You will be contacted by our delivery agent shortly."
    cart = db.get_cart(str(message.chat.id))
    order_id = db.new_order(message.chat.id, cart["total_cost"],
                            db.get_cart_items(message.chat.id))
    alert_admins_of_new_order(order_id)
    db.remove_item_from_cart(
        message.chat.id, *([product['id'] for product in cart['products']]))

    bot.send_message(chat_id=message.chat.id, text=text)
    display_main_menu(message.chat.id, "What would you like to do next?")


# admin handlers

def display_admin_menu(chat_id, text):
    menu_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=2)

    menu_markup.add("Add Item", "Remove Item", "Update Item", "View All Items",
                    "Pending Orders", "Confirmed Orders", "Cancelled Orders", "Completed Orders")
    menu_markup.row("All Orders")

    modify_step(chat_id, "admin", reset=True)

    bot.send_message(chat_id=chat_id, text=text, reply_markup=menu_markup)


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "admin_password")
def admin_password_handler(message):
    if message.text != config.ADMIN_PASSWORD:
        text = "Incorrect password, please try again"
        bot.send_message(chat_id=message.chat.id, text=text)
        return

    db.set_user_as_admin(message.chat.id)

    bot.send_message(chat_id=message.chat.id, text="Access granted")
    display_admin_menu(message.chat.id, "What would you like to do?")


@bot.message_handler(
    func=lambda message: message.text == "Add Item" and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "admin")
def add_item_handler(message):
    text = "Please enter the item name"
    modify_step(message.chat.id, "add_item_name")
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step.get(str(message.chat.id))[
        "current"] == "add_item_name")
def add_item_name_handler(message):
    new_product['name'] = message.text
    text = f"Enter the description of {new_product['name']}"
    modify_step(message.chat.id, "add_item_description")
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step.get(str(message.chat.id))[
        "current"] == "add_item_description")
def add_item_description_handler(message):
    new_product['description'] = message.text
    text = f"Enter the price of {new_product['name']}"
    modify_step(message.chat.id, "add_item_price")
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step.get(str(message.chat.id))[
        "current"] == "add_item_price")
def add_item_price_handler(message):
    new_product['price'] = message.text
    text = f"Send an image of {new_product['name']}"
    modify_step(message.chat.id, "add_item_image")
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(content_types=['photo'],
                     func=lambda message: step.get(str(message.chat.id)) and step.get(str(message.chat.id))[
                         "current"] == "add_item_image")
def upload_product_image(message):
    file_id = message.photo[-1].file_id
    file_path = bot.get_file(file_id).file_path
    full_file_path = f"https://api.telegram.org/file/bot{config.API_KEY}/{file_path}"
    res = media_handler.upload_image(
        full_file_path, public_id=new_product['name'])
    db.new_product(name=new_product['name'], description=new_product['description'],
                   price=new_product['price'], image=res['secure_url'])
    text = f"{new_product['name']} has been added to the list of products"
    display_admin_menu(message.chat.id, text)


@bot.message_handler(func=lambda message: message.text == "View All Items" and step.get(str(message.chat.id)) and
                                          step[str(message.chat.id)]["current"] == "admin")
def view_all_items_handler(message):
    products = db.get_products()
    if not products:
        bot.send_message(chat_id=message.chat.id,
                         text="There are no items in the store")
        display_admin_menu(message.chat.id, "What would you like to do next?")
        return

    text = "Here are the list of items in the store\n\n"

    for product in products:
        text += f"Name: {product}\nDescription: {products[product]['description']}\n" \
                f"Price: {products[product]['price']}\n\n"
    bot.send_message(chat_id=message.chat.id, text=text)
    display_admin_menu(message.chat.id, "What would you like to do next?")


@bot.message_handler(func=lambda message: message.text == "Remove Item" and step.get(str(message.chat.id)) and
                                          step[str(message.chat.id)]["current"] == "admin")
def remove_item_handler(message):
    text = "Please select item you want to remove"
    modify_step(message.chat.id, "remove_item_name")

    items = db.get_products()
    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=2)
    for item in items:
        reply_markup.add(item)
    reply_markup.row("Return to Admin Menu")
    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(
    func=lambda message: message.text == "All Orders" and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "admin")
def all_orders_handler(message):
    orders = db.get_orders()
    if not orders:
        bot.send_message(chat_id=message.chat.id,
                         text="There are no orders")
        display_admin_menu(message.chat.id, "What would you like to do next?")
        return

    text = "Here are the list of orders\n\n"

    for order in orders:
        text += f"Order ID: {order}\nUser ID: {orders[order]['user_id']}\nOrder State: {orders[order]['state']}\n\n"
    bot.send_message(chat_id=message.chat.id, text=text)
    display_admin_menu(message.chat.id, "What would you like to do next?")


@bot.message_handler(commands=['activate_notifications'],
                     func=lambda message: step.get(str(message.chat.id)) and step[str(message.chat.id)][
                         "current"] == "admin")
def activate_notifications_handler(message):
    db.activate_notifications(message.chat.id)
    bot.send_message(
        message.chat.id, "You would receive order notifications on this chat")


@bot.message_handler(commands=['deactivate_notifications'],
                     func=lambda message: step.get(str(message.chat.id)) and step[str(message.chat.id)][
                         "current"] == "admin")
def deactivate_notifications_handler(message):
    db.deactivate_notifications(message.chat.id)
    bot.send_message(
        message.chat.id, "You would not receive order notifications on this chat")


@bot.message_handler(func=lambda message: message.text == "Pending Orders" and step.get(str(message.chat.id)) and
                                          step[str(message.chat.id)]["current"] == "admin")
def pending_orders_handler(message):
    orders = db.get_orders(state="pending")
    if not orders:
        bot.send_message(chat_id=message.chat.id,
                         text="There are no pending orders")
        display_admin_menu(message.chat.id, "What would you like to do next?")
        return

    text = "Here are the list of pending orders\n\n"
    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=2)
    modify_step(message.chat.id, "order_selection")

    for order in orders:
        text += f"Order ID: {order}\nUser ID: {orders[order]['user_id']}\n\n"
        reply_markup.add(str(order))

    reply_markup.row("Return to Admin Menu")
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=reply_markup)


@bot.message_handler(func=lambda message: message.text == "Completed Orders" and step.get(str(message.chat.id)) and
                                          step[str(message.chat.id)]["current"] == "admin")
def completed_orders_handler(message):
    orders = db.get_orders(state="completed")
    if not orders:
        bot.send_message(chat_id=message.chat.id,
                         text="There are no completed orders")
        display_admin_menu(message.chat.id, "What would you like to do next?")
        return

    text = "Here are the list of completed orders\n\nSelect an order to view details\n\n"
    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=2)
    modify_step(message.chat.id, "order_selection")

    for order in orders:
        text += f"Order ID: {order}\nUser ID: {orders[order]['user_id']}\n\n"
        reply_markup.add(str(order))
    reply_markup.row("Return to Admin Menu")

    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=reply_markup)


@bot.message_handler(func=lambda message: message.text == "Cancelled Orders" and step.get(str(message.chat.id)) and
                                          step[str(message.chat.id)]["current"] == "admin")
def cancelled_orders_handler(message):
    orders = db.get_orders(state="cancelled")
    if not orders:
        bot.send_message(chat_id=message.chat.id,
                         text="There are no cancelled orders")
        display_admin_menu(message.chat.id, "What would you like to do next?")
        return

    text = "Here are the list of cancelled orders\n\nSelect an order to view details\n\n"
    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=2)
    modify_step(message.chat.id, "order_selection")

    for order in orders:
        text += f"Order ID: {order}\nUser ID: {orders[order]['user_id']}\n\n"
        reply_markup.add(str(order))
    reply_markup.row("Return to Admin Menu")

    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=reply_markup)


@bot.message_handler(func=lambda message: message.text == "Confirmed Orders" and step.get(str(message.chat.id)) and
                                          step[str(message.chat.id)]["current"] == "admin")
def confirmed_orders_handler(message):
    orders = db.get_orders(state="confirmed")
    if not orders:
        bot.send_message(chat_id=message.chat.id,
                         text="There are no confirmed orders")
        display_admin_menu(message.chat.id, "What would you like to do next?")
        return

    text = "Here are the list of confirmed orders\n\nSelect an order to view details\n\n"
    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=2)
    modify_step(message.chat.id, "order_selection")

    for order in orders:
        text += f"Order ID: {order}\nUser ID: {orders[order]['user_id']}\n\n"
        reply_markup.add(str(order))
    reply_markup.row("Return to Admin Menu")

    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=reply_markup)


@bot.message_handler(func=lambda message: message.text.isdecimal() and step.get(str(message.chat.id)) and
                                          step[str(message.chat.id)]["current"] == "order_selection")
def order_selection_handler(message):
    order_id = message.text
    order = db.get_order(order_id)
    if not order:
        bot.send_message(chat_id=message.chat.id,
                         text="Order does not exist, please try again")
        return

    text = f"Order ID: {order_id}\nUser ID: {order['user_id']}\nOrder State: {order['state']}\n\n" \
           f"Order Items:\n\n"
    for item in order["items"]:
        text += f"Item: {item['product']}\nQuantity: {item['quantity']}\nPrice: {item['price']}\n\n"
    reply_markup = telebot.types.InlineKeyboardMarkup()
    reply_buttons = ["Complete Order", "Cancel Order", "Confirm Order", "Pending Order"]
    for btn in reply_buttons:
        reply_markup.add(
            telebot.types.InlineKeyboardButton(btn, callback_data=str({"order_id": order_id, "action": btn})))

    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=reply_markup)


def alert_user_of_order_state_change(order_id, state):
    order = db.get_order(order_id)
    if not order:
        return

    user_id = order["user_id"]
    user = db.get_user(user_id)
    if not user:
        return

    text = f"Your order {order_id} has been marked as {state}"
    bot.send_message(chat_id=user_id, text=text)


@bot.callback_query_handler(
    func=lambda call: eval(call.data)["action"] in ["Complete Order", "Cancel Order", "Confirm Order", "Pending Order"])
def order_callback_handler(call):
    data = eval(call.data)
    order_id = data["order_id"]
    state = data["action"].split(" ")[0].lower()
    match data["action"]:
        case "Complete Order":
            db.update_order(order_id, state="completed")
            state = "completed"
        case "Cancel Order":
            db.update_order(order_id, state="cancelled")
            state = "cancelled"
        case "Confirm Order":
            db.update_order(order_id, state="confirmed")
            state = "confirmed"
        case "Pending Order":
            db.update_order(order_id, state="pending")
            state = "pending"
    bot.answer_callback_query(call.id, "Order state has been updated")
    alert_user_of_order_state_change(order_id, state)
    display_admin_menu(call.message.chat.id, "What would you like to do next?")
    bot.answer_callback_query(call.id)


@bot.message_handler(
    func=lambda message: message.text == "Return to Admin Menu" and step.get(str(message.chat.id)) and db.get_user(
        message.chat.id).is_admin)
def return_to_admin_menu(message):
    display_admin_menu(message.chat.id, "What would you like to do next?")


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step.get(str(message.chat.id))[
        "current"] == "remove_item_name")
def remove_item_name_handler(message):
    from models import Product

    product_id = db.session.query(Product).filter_by(name=message.text).first().id
    db.remove_product(product_id)

    text = f"{message.text} has been removed from the list of products"
    display_admin_menu(message.chat.id, text)


# catch all handler
@bot.message_handler(func=lambda m: True)
def default_handler(message):
    text = "Sorry, I didn't understand that command.\n\nPlease select an option from the menu below."
    display_main_menu(message.chat.id, text)


if config.ENV == "development":
    bot.remove_webhook()
    bot.polling()
else:
    bot.remove_webhook()
    bot.set_webhook(config.WEBHOOK_URL)
