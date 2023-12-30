""" This is the main file for the bot 
    Run this file to start the bot when in development
"""

# pylint: disable = missing-function-docstring, line-too-long

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

# Firebase does not support threading for cloud functions
bot = telebot.TeleBot(token=config.API_KEY, threaded=False)

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

step = {}

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

def display_main_menu(chat_id: str, text: str):
    """
    Displays the main menu to the user.

    Parameters:
    - chat_id (str): The ID of the chat.
    - text (str): The text to display in the message.

    Returns:
    None
    """

    menu_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=2)

    menu_markup.row("Make A Purchase")
    menu_markup.add("View Cart", "Checkout")

    bot.send_message(chat_id=chat_id, text=text, reply_markup=menu_markup)


def display_products(chat_id: str):
    """
    Displays a list of products to the user in a Telegram chat.

    Parameters:
    - chat_id (str): The ID of the chat where the products will be displayed.

    Returns:
    None
    """

    products_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select A Product", row_width=2)

    product_list = db.get_products()
    products = {product.name: {"price": product.price, "description": product.description,
                               "image": product.image, "id": product.id_} for product in product_list}
    products_markup.add(*products)

    products_markup.row("Checkout", "View Cart")
    products_markup.row("Main Menu")

    text = "Hello, what would you like to purchase?\nSelect a product from the list below"

    db.update_user_navigation(chat_id, "display_products")

    bot.send_message(chat_id=chat_id, text=text, reply_markup=products_markup)


def display_cart(chat_id: str):
    """
    Display the contents of the cart for a given chat ID.

    Args:
        chat_id (str): The ID of the chat.

    Returns:
        None
    """

    cart = db.get_cart(chat_id)

    if not cart['products']:
        text = "Your cart is empty"
        bot.send_message(chat_id=chat_id, text=text)
        return

    text = f"Total Cost: {cart['total_cost']}\n\n"
    for cart_item in cart["products"]:
        text += f"Product: {cart_item.product.name}\nQuantity: {cart_item.quantity}\n\n"

    bot.send_message(chat_id=int(chat_id), text=text)


@bot.message_handler(commands=['start'])
def start_handler(message: telebot.types.Message):
    """
    Handles the start command from the user.

    Args:
        message (telebot.types.Message): The message object received from the user.

    Returns:
        None
    """

    if db.get_user_by_id(str(message.chat.id)) is None:
        fullname = f"{message.from_user.first_name} {message.from_user.last_name if message.from_user.last_name else ''}"
        db.create_new_user(str(message.chat.id), display_name=fullname)

    text = f"Hello {message.from_user.first_name}, welcome to our store.\n\nWhat would you like to do?"

    display_main_menu(str(message.chat.id), text)


@bot.message_handler(commands=['cancel'])
def cancel_handler(message: telebot.types.Message):
    """
    Handles the cancel command from the user.

    Args:
        message (telebot.types.Message): The message object received from the user.
    """
    display_main_menu(str(message.chat.id), "What would you like to do next?")


@bot.message_handler(commands=['help'])
def send_welcome(message: telebot.types.Message):
    """
    Sends a welcome message to the user.

    Parameters:
    - message: telebot.types.Message object representing the incoming message.

    Returns:
    None
    """
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda message: message.text == "Make A Purchase")
def make_purchase_handler(message: telebot.types.Message):
    """
    Handles the logic for making a purchase.

    Args:
        message (telebot.types.Message): The message object containing the user's input.

    Returns:
        None
    """
    db.update_user_navigation(str(message.chat.id), "make_purchase")
    display_products(str(message.chat.id))


@bot.message_handler(func=lambda message: message.text in ("Checkout", "Proceed To Checkout"))
def checkout_handler(message: telebot.types.Message):
    """
    Handles the checkout process for the user.

    Args:
        message (telebot.types.Message): The message object received from the user.

    Returns:
        None
    """

    db.update_user_navigation(str(message.chat.id), "checkout")
    cart = db.get_cart(str(message.chat.id))

    if not cart['products']:
        text = "Your cart is empty"
        display_main_menu(str(message.chat.id), text)
        return
    user = db.get_user_by_id(str(message.chat.id))

    if not user:
        bot.send_message(chat_id=message.chat.id,
                         text="An error occurred, please try again")
        display_main_menu(str(message.chat.id),
                          "What would you like to do next?")
        return

    text = "Please enter your phone number to proceed with payment\n\nFormat: 0201234567"
    db.update_user_navigation(str(message.chat.id), "phone_number")

    reply_markup = telebot.types.ForceReply(input_field_placeholder="Enter Phone Number")

    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(func=lambda message: message.text == "View Cart")
def view_cart_handler(message: telebot.types.Message):
    """
    Handles the view cart functionality.

    Args:
        message (telebot.types.Message): The message object received from the user.
    """

    db.update_user_navigation(str(message.chat.id), "view_cart")

    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=1)
    reply_markup.add("Main Menu")

    reply_markup.add("Proceed To Checkout")
    display_cart(str(message.chat.id))
    display_main_menu(str(message.chat.id), "What would you like to do next?")


@bot.message_handler(func=lambda message: message.text == "Main Menu")
def main_menu_handler(message: telebot.types.Message):
    """
    Handles the main menu functionality.

    Args:
        message (telebot.types.Message): The incoming message object.
    """
    display_main_menu(str(message.chat.id), "What would you like to do next?")


@bot.message_handler(
    func=lambda message: message.text and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "display_products")
def product_selection_handler(message: telebot.types.Message):
    """
    Handles the selection of a product by the user.

    Args:
        message (telebot.types.Message): The message object containing the user's input.

    Returns:
        None
    """

    if message.text is None:
        return
    print(message.text)
    products = db.get_products_by_name(message.text)
    print(products)
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

    db.create_order_in_progress(str(message.chat.id), product)

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
    db.update_order_in_progress(chat_id, quantity=int(message.text))
    orders_in_progress = db.get_order_in_progress(chat_id)
    if not orders_in_progress:
        bot.send_message(chat_id=message.chat.id,
                         text="An error occurred, please try again")
        display_main_menu(str(message.chat.id),
                          "What would you like to do next?")
        return

    total_cost = int(message.text) * \
        decimal.Decimal(orders_in_progress.product.price)

    text = f"{orders_in_progress.product.name}\nQuantity: {message.text}\nTotal Cost: {total_cost}\n\nWould you like to add this to your cart?"

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
        orders_in_progress = db.get_order_in_progress(chat_id)
        if not orders_in_progress:
            bot.send_message(chat_id=message.chat.id,
                             text="An error occurred, please try again")
            display_main_menu(
                str(message.chat.id), "What would you like to do next?")
            return

        db.add_to_cart(chat_id, orders_in_progress.product.id_,
                       orders_in_progress.quantity, decimal.Decimal(0))

        text = "Product added to cart"

    else:
        text = "Product not added to cart"

    db.remove_order_in_progress(chat_id)

    modify_step(str(message.chat.id), "add_to_cart")

    bot.send_message(chat_id=message.chat.id, text=text)
    display_main_menu(
        str(message.chat.id), text="What would you like to do next?\nSelect checkout to proceed with payment")


@bot.message_handler(
    func=lambda message: message.text == "Back" and step[str(message.chat.id)]["current"] == "product_selection")
def quantity_selection_back_handler(message: telebot.types.Message):
    db.remove_order_in_progress(str(message.chat.id))
    display_products(str(message.chat.id))


@bot.message_handler(
    func=lambda message: message.text and message.reply_to_message and ("phone" in message.reply_to_message.text.lower()))
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
    reply_markup = telebot.types.ForceReply(input_field_placeholder="Enter Address")
    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(
    func=lambda message: message.text and message.reply_to_message and ("address" in message.reply_to_message.text.lower()))
def address_handler(message: telebot.types.Message):
    chat_id = str(message.chat.id)

    if message.text is None:
        return

    address = message.text

    user = db.update_user(chat_id, address=address)

    text = "Please enter your name\n\nFormat: First Name Last Name\n\nExample: John Doe"
    reply_markup = telebot.types.ForceReply(input_field_placeholder="Enter Name")
    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(
    func=lambda message: message.text and message.reply_to_message and ("name" in message.reply_to_message.text.lower()))
def name_handler(message: telebot.types.Message):
    if message.text is None:
        return

    chat_id = str(message.chat.id)
    name = message.text

    user = db.update_user(chat_id, display_name=name)


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


@bot.message_handler(func=lambda message: message.text == "Cancel Order" and step.get(str(message.chat.id)) and step[str(message.chat.id)][
    "current"] == "confirm_order")
def cancel_order_handler(message: telebot.types.Message):
    db.remove_order_in_progress(str(message.chat.id))
    display_main_menu(str(message.chat.id), "What would you like to do next?")


@bot.message_handler(
    func=lambda message: message.text == "Proceed" and step.get(str(message.chat.id)) and step[str(message.chat.id)][
        "current"] == "confirm_order")
def confirm_order_handler(message: telebot.types.Message):
    cart = db.get_cart(str(message.chat.id))
    order_id = db.create_order(
        str(message.chat.id), cart["total_cost"], db.get_cart_items(str(message.chat.id)))
    text = f"Your order with ID {order_id[:5]} is being processed. You will be contacted by our delivery agent shortly."

    for product in cart["products"]:
        db.remove_item_from_cart(str(message.chat.id), product)

    bot.send_message(chat_id=message.chat.id, text=text)
    display_main_menu(str(message.chat.id), "What would you like to do next?")


@bot.message_handler(commands=['admin_login'], func=lambda message: message.text == config.ADMIN_PASSWORD)
def register_chat_as_admin(message: telebot.types.Message):
    """
    Registers a chat as an admin chat.

    Args:
        message (telebot.types.Message): The message object received from the user.

    Returns:
        None
    """

    db.update_user(str(message.chat.id), is_admin=1)

    text = "You have been registered as an admin"
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(commands=['admin_login'], func=lambda message: message.text != config.ADMIN_PASSWORD)
def register_chat_as_admin_incorrect_password(message: telebot.types.Message):
    """
    Registers a chat as an admin chat.

    Args:
        message (telebot.types.Message): The message object received from the user.

    Returns:
        None
    """

    text = "Incorrect password"
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(commands=['admin_logout'], func=lambda message: message.text == config.ADMIN_PASSWORD)
def unregister_chat_as_admin(message: telebot.types.Message):
    """
    Unregisters a chat as an admin chat.

    Args:
        message (telebot.types.Message): The message object received from the user.

    Returns:
        None
    """

    db.update_user(str(message.chat.id), is_admin=0)

    text = "You have been unregistered as an admin"
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
