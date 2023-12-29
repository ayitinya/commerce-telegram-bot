""" This is the main file for the bot 
    Run this file to start the bot when in development
"""

# pylint: disable = missing-function-docstring

import decimal
import logging

import telebot

import config
from data.DatabaseInterface import DatabaseFactory
from data.firestore import Firestore
from media_handler import FirebaseStorage, MediaHandlerFactory

db = DatabaseFactory(Firestore).get_database()
media_handler = MediaHandlerFactory(FirebaseStorage).get_handler()

if not config.API_KEY:
    raise ValueError("API_KEY is not set")

bot = telebot.TeleBot(config.API_KEY, threaded=False)

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

step = {}
new_product = {}
orders_in_progress = {}


def modify_step(chat_id: str, new_step: str, reset=False):

    if chat_id not in step:
        step[chat_id] = {"current": "", "path": []}

    if reset:
        step[chat_id] = {"current": "", "path": []}
        step[chat_id]["path"].append(new_step)
        step[chat_id]["current"] = new_step
        return

    step[chat_id]["current"] = new_step
    step[chat_id]["path"].append(new_step)


def display_main_menu(chat_id: str, text: str):
    menu_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=2)

    menu_markup.row("Make A Purchase")
    menu_markup.add("View Cart", "Checkout")

    modify_step(chat_id, "start", reset=True)

    bot.send_message(chat_id=chat_id, text=text, reply_markup=menu_markup)


def display_products(chat_id: str):
    products_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select A Product", row_width=2)

    product_list = db.get_products()
    products_markup.add(*product_list)

    products_markup.row("Checkout", "View Cart")
    products_markup.row("Main Menu")

    text = "Hello, what would you like to purchase?\nSelect a product from the list below"

    modify_step(chat_id, "display_products")

    bot.send_message(chat_id=chat_id, text=text, reply_markup=products_markup)


def display_cart(chat_id: str):
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
def start_handler(message: telebot.types.Message):
    if db.get_user_by_id(str(message.chat.id)) is None:
        fullname = f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
        db.create_new_user(str(message.chat.id), display_name=fullname)

    text = f"Hello {message.from_user.first_name}, welcome to our store.\n\nWhat would you like to do?"

    display_main_menu(str(message.chat.id), text)


@bot.message_handler(commands=['cancel'])
def cancel_handler(message: telebot.types.Message):
    user = db.get_user_by_id(str(message.chat.id))
    if user and user.is_admin:
        display_admin_menu(str(message.chat.id), "What would you like to do next?")
        return
    display_main_menu(str(message.chat.id), "What would you like to do next?")


@bot.message_handler(commands=['admin'])
def admin_handler(message: telebot.types.Message):
    if db.get_user_by_id(str(message.chat.id)) is None:
        fullname = f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
        db.create_new_user(str(message.chat.id), display_name=fullname)

    text = "Welcome Admin, enter the password to continue"
    modify_step(str(message.chat.id), "admin_password", reset=True)
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(commands=['help'])
def send_welcome(message: telebot.types.Message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda message: message.text == "Make A Purchase")
def make_purchase_handler(message: telebot.types.Message):
    modify_step(str(message.chat.id), "make_purchase")
    display_products(str(message.chat.id))


@bot.message_handler(func=lambda message: message.text in ("Checkout", "Proceed To Checkout"))
def checkout_handler(message: telebot.types.Message):
    modify_step(str(message.chat.id), "checkout")
    cart = db.get_cart(str(message.chat.id))

    if not cart['products']:
        text = "Your cart is empty"
        display_main_menu(str(message.chat.id), text)
        return
    user = db.get_user_by_id(str(message.chat.id))

    if not user:
        bot.send_message(chat_id=message.chat.id,
                         text="An error occurred, please try again")
        display_main_menu(str(message.chat.id), "What would you like to do next?")
        return

    text = "Please enter your phone number to proceed with payment\n\nFormat: 0201234567"
    modify_step(str(message.chat.id), "phone_number")

    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Enter Phone Number")

    if user.phone:
        reply_markup.add(user.phone)
    reply_markup.add("Main Menu")
    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(func=lambda message: message.text == "View Cart")
def view_cart_handler(message: telebot.types.Message):
    modify_step(str(message.chat.id), "view_cart")

    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=1)
    reply_markup.add("Main Menu")

    reply_markup.add("Proceed To Checkout")
    display_cart(str(message.chat.id))
    display_main_menu(str(message.chat.id), "What would you like to do next?")


@bot.message_handler(func=lambda message: message.text == "Main Menu")
def main_menu_handler(message: telebot.types.Message):
    display_main_menu(str(message.chat.id), "What would you like to do next?")


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "display_products")
def product_selection_handler(message: telebot.types.Message):
    if message.text is None:
        return
    products = db.get_products_by_name(message.text)
    if not products:
        bot.send_message(chat_id=message.chat.id,
                         text="Product not found, please try again")
        return
    product = products[0]

    reply = f"Product: {message.text}\nPrice: {product.price}\n\nHow many would you like to purchase?"

    image = media_handler.download(product.image)

    quantity_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Enter Quantity", row_width=3)
    quantity_markup.add(*[str(i) for i in range(1, 11)], "Back")

    modify_step(str(message.chat.id), "product_selection")

    orders_in_progress[str(message.chat.id)] = {
        "product": message.text,
        "price": product.price,
        "quantity": 0
    }
    bot.send_photo(message.chat.id, image, caption=reply,
                   reply_markup=quantity_markup)


@bot.message_handler(
    func=lambda message: message.text.isdecimal() and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "product_selection")
def quantity_selection_handler(message: telebot.types.Message):
    if message.text is None:
        return

    modify_step(str(message.chat.id), "quantity_selection")

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
def add_to_cart_handler(message: telebot.types.Message):
    chat_id = str(message.chat.id)

    if message.text == "Yes":
        if chat_id not in orders_in_progress:
            bot.send_message(chat_id=message.chat.id,
                             text="An error occurred, please try again")
            display_main_menu(
                str(message.chat.id), "What would you like to do next?")
            return

        db.add_to_cart(chat_id, orders_in_progress[chat_id]["product"],
                       orders_in_progress[chat_id]["quantity"], orders_in_progress[chat_id]["price"])

        text = "Product added to cart"

    else:
        text = "Product not added to cart"

    orders_in_progress[chat_id] = None

    modify_step(str(message.chat.id), "add_to_cart")

    bot.send_message(chat_id=message.chat.id, text=text)
    display_main_menu(
        str(message.chat.id), text="What would you like to do next?\nSelect checkout to proceed with payment")


@bot.message_handler(
    func=lambda message: message.text == "Back" and step[str(message.chat.id)]["current"] == "product_selection")
def quantity_selection_back_handler(message: telebot.types.Message):
    orders_in_progress[str(message.chat.id)] = None
    display_products(str(message.chat.id))


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "phone_number")
def phone_number_handler(message: telebot.types.Message):
    chat_id = str(message.chat.id)
    phone = message.text
    if phone is None:
        return

    if len(phone) != 10 or not phone.isdecimal():
        text = "Please enter a valid phone number\n\nFormat: 0201234567"
        bot.send_message(chat_id=message.chat.id, text=text)
        return

    user = db.update_user(chat_id, phone=phone)

    modify_step(str(message.chat.id), "address")
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
def address_handler(message: telebot.types.Message):
    chat_id = str(message.chat.id)

    if message.text is None:
        return

    address = message.text

    user = db.update_user(chat_id, address=address)

    modify_step(str(message.chat.id), "name")
    text = "Please enter your name\n\nFormat: First Name Last Name\n\nExample: John Doe"
    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option")
    reply_markup.row(user.display_name)
    reply_markup.row("Main Menu")
    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "name")
def name_handler(message: telebot.types.Message):
    if message.text is None:
        return

    chat_id = str(message.chat.id)
    name = message.text

    user = db.update_user(chat_id, display_name=name)

    modify_step(str(message.chat.id), "confirm_order")

    text = "Your order of"
    bot.send_message(chat_id=message.chat.id, text=text)
    display_cart(str(message.chat.id))
    text = f"will be delivered to\n\n{user.display_name}\n\n{user.address}\n\n{user.phone}\n\nPlease confirm your order"
    bot.send_message(chat_id=message.chat.id, text=text)
    text = "Due to current limitations, we only accept cash payments." \
           "Once you confirm your order, you will be contacted by our delivery agent to arrange payment and delivery."

    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select Payment Method", row_width=1)
    reply_markup.add("Cancel Order")
    reply_markup.add("Proceed")

    modify_step(str(message.chat.id), "confirm_order")
    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(
    func=lambda message: message.text == "Proceed" and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "confirm_order")
def confirm_order_handler(message: telebot.types.Message):
    cart = db.get_cart(str(message.chat.id))
    order_id = db.create_order(str(message.chat.id), cart["total_cost"], db.get_cart_items(str(message.chat.id)))
    text = f"Your order with ID {order_id[:5]} is being processed. You will be contacted by our delivery agent shortly."

    # alert_admins_of_new_order(order_id)
    db.remove_item_from_cart(
        str(message.chat.id), *([product['id'] for product in cart['products']]))

    bot.send_message(chat_id=message.chat.id, text=text)
    display_main_menu(str(message.chat.id), "What would you like to do next?")


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
def admin_password_handler(message: telebot.types.Message):
    if message.text != config.ADMIN_PASSWORD:
        text = "Incorrect password, please try again"
        bot.send_message(chat_id=message.chat.id, text=text)
        return

    db.authenticate_user(str(message.chat.id))

    bot.send_message(chat_id=message.chat.id, text="Access granted")
    display_admin_menu(str(message.chat.id), "What would you like to do?")

# update item


@bot.message_handler(func=lambda message: message.text == "Update Item" and step.get(str(message.chat.id)) and step[str(message.chat.id)]["current"] == "admin")
def update_item_handler(message: telebot.types.Message):
    products = db.get_products()
    modify_step(str(message.chat.id), "update_item")
    if not products:
        bot.send_message(chat_id=message.chat.id,
                         text="There are no items to be edited")
        display_admin_menu(str(message.chat.id), "What would you like to do next?")
        return

    text = "Enter number of item to be edited\n\n"

    for index, product in enumerate(products):
        text += f"{index}. Name: {product.name}\nDescription: {product.description}\n" \
                f"Price: {product.price}\n\n"

    bot.send_message(chat_id=message.chat.id, text=text)


# catch all handler
@bot.message_handler(func=lambda m: True)
def default_handler(message: telebot.types.Message):
    text = "Sorry, I didn't understand that command.\n\nPlease select an option from the menu below."
    display_main_menu(str(message.chat.id), text)


if config.ENV == "development":
    bot.remove_webhook()
    bot.polling()
else:
    if bot.get_webhook_info().url != config.WEBHOOK_URL:
        bot.delete_webhook()
        bot.set_webhook(config.WEBHOOK_URL)
