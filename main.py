from dotenv import load_dotenv

import os
import telebot
import logging


load_dotenv()


API_KEY = os.getenv('API_KEY')

bot = telebot.TeleBot(API_KEY)

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

step = {}
users = {}

products = {
    "Perfume": {
        "price": 30,
        "stock": 10,
    },
    "Shoes": {
        "price": 54,
        "stock": 10,
    },
    "Clothes": {
        "price": 95.2,
        "stock": 10,
    },
    "Jewelry": {
        "price": 23,
        "stock": 10,
    },
    "Accessories": {
        "price": 100,
        "stock": 10,
    },
    "Footballs": {
        "price": 43.23,
        "stock": 10,
    },

}

orders_in_progress = {}
cart = {}


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

    product_list = products.keys()
    products_markup.add(*product_list)

    products_markup.row("Checkout", "View Cart")
    products_markup.row("Main Menu")

    text = "Hello, what would you like to purchase?\nSelect a product from the list below"

    modify_step(chat_id, "display_products")

    bot.send_message(chat_id=chat_id, text=text, reply_markup=products_markup)


def display_cart(chat_id,):

    chat_id = str(chat_id)

    text = f"Total Cost: {cart[chat_id]['total_cost']}\n\n"
    for product in cart[chat_id]["products"]:
        text += f"Product: {product['product']}\nQuantity: {product['quantity']}\n\n"

    bot.send_message(chat_id=int(chat_id), text=text)


@bot.message_handler(commands=['start'])
def start_handler(message):

    text = f"Hello {message.from_user.first_name}, welcome to our store.\n\nWhat would you like to do?"

    display_main_menu(message.chat.id, text)


@bot.message_handler(func=lambda message: message.text == "Make A Purchase")
def make_purchase_handler(message):
    modify_step(message.chat.id, "make_purchase")
    display_products(message.chat.id)


@bot.message_handler(func=lambda message: message.text in products.keys())
def product_selection_handler(message):
    reply = f"Product: {message.text}\nPrice: {products[message.text]['price']}\n\nHow many would you like to purchase?"

    quantity_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Enter Quantity", row_width=3)
    quantity_markup.add(*[str(i) for i in range(1, 11)], "Back")

    modify_step(message.chat.id, "product_selection")

    orders_in_progress[str(message.chat.id)] = {
        "product": message.text,
        "quantity": 0
    }

    bot.send_message(message.chat.id, reply, reply_markup=quantity_markup)


@bot.message_handler(func=lambda message: message.text.isdecimal() and step[str(message.chat.id)]["current"] == "product_selection")
def quantity_selection_handler(message):
    modify_step(message.chat.id, "quantity_selection")

    chat_id = str(message.chat.id)
    orders_in_progress[chat_id]["quantity"] = int(message.text)
    product = orders_in_progress[chat_id]["product"]
    product_price = products[product]["price"]
    total_cost = int(message.text) * product_price

    text = f"{product}\nQuantity: {message.text}\nTotal Cost: {total_cost}\n\nWould you like to add this to your cart?"

    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option")
    reply_markup.row("Yes", "No")
    reply_markup.row("Back")

    bot.send_message(chat_id=message.chat.id, text=text,
                     reply_markup=reply_markup)


@bot.message_handler(func=lambda message: message.text == "Yes" or message.text == "No" and step[str(message.chat.id)]["current"] == "quantity_selection")
def add_to_cart_handler(message):

    chat_id = str(message.chat.id)

    if message.text == "Yes":
        if chat_id not in cart:
            cart[chat_id] = {"total_cost": 0, "products": []}

        cart[chat_id]["total_cost"] += orders_in_progress[chat_id]["quantity"] * \
            products[orders_in_progress[chat_id]["product"]]["price"]
        cart[chat_id]["products"].append(
            {"product": orders_in_progress[chat_id]["product"], "quantity": orders_in_progress[chat_id]["quantity"]})

        text = "Product added to cart"

    else:
        text = "Product not added to cart"

    orders_in_progress[chat_id] = None

    modify_step(message.chat.id, "add_to_cart")

    bot.send_message(chat_id=message.chat.id, text=text)
    display_main_menu(
        message.chat.id, text="What would you like to do next?\nSelect checkout to proceed with payment")


@bot.message_handler(func=lambda message: message.text == "View Cart")
def view_cart_handler(message):
    modify_step(message.chat.id, "view_cart")

    chat_id = str(message.chat.id)

    reply_markup = telebot.types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select An Option", row_width=1)
    reply_markup.add("Main Menu")

    if chat_id not in cart:
        text = "Your cart is empty"
        bot.send_message(chat_id=message.chat.id, text=text,
                         reply_markup=reply_markup)
        return

    reply_markup.add("Proceed To Checkout")
    display_cart(message.chat.id)
    display_main_menu(message.chat.id, "What would you like to do next?")


@bot.message_handler(func=lambda message: message.text == "Main Menu")
def main_menu_handler(message):
    display_main_menu(message.chat.id, "What would you like to do next?")


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda message: message.text == "Back" and step[str(message.chat.id)]["current"] == "product_selection")
def quantity_selection_back_handler(message):
    orders_in_progress[str(message.chat.id)] = None
    display_products(message.chat.id)


@bot.message_handler(func=lambda message: message.text == "Checkout" or message.text == "Proceed To Checkout")
def checkout_handler(message):
    modify_step(message.chat.id, "checkout")
    chat_id = str(message.chat.id)

    if chat_id not in cart:
        text = "Your cart is empty"
        display_main_menu(message.chat.id, text)
        return
    
    if chat_id not in users:
        users[chat_id] = {"phone_number": None, "address": None, "name": None}
        
    text = "Please enter your phone number to proceed with payment\n\nFormat: 0201234567"
    modify_step(message.chat.id, "phone_number")
    
    reply_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Enter Phone Number")
    reply_markup.add(users[chat_id]["phone_number"]) if users[chat_id]["phone_number"] else None
    reply_markup.add("Main Menu")
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=reply_markup)
    

@bot.message_handler(func=lambda message: message.text and step[str(message.chat.id)]["current"] == "phone_number")
def phone_number_handler(message):
    chat_id = str(message.chat.id)
    phone_number= message.text
    
    if len(phone_number) != 10 or not phone_number.isdecimal():
        text = "Please enter a valid phone number\n\nFormat: 0201234567"
        bot.send_message(chat_id=message.chat.id, text=text)
        return
    
    users[chat_id]["phone_number"] = phone_number
    
    modify_step(message.chat.id, "address")
    text = "Please enter your address\n\nFormat: 1234 Street Name, City, Region\n\nExample: 1234 Street Name, Accra, Greater Accra"
    bot.send_message(chat_id=message.chat.id, text=text)
    

@bot.message_handler(func=lambda message: message.text and step[str(message.chat.id)]["current"] == "address")
def address_handler(message):
    chat_id = str(message.chat.id)
    address = message.text
    
    users[chat_id]["address"] = address
    
    modify_step(message.chat.id, "name")
    text = "Please enter your name\n\nFormat: First Name Last Name\n\nExample: John Doe"
    bot.send_message(chat_id=message.chat.id, text=text)


@bot.message_handler(func=lambda message: message.text and step[str(message.chat.id)]["current"] == "name")
def name_handler(message):
    chat_id = str(message.chat.id)
    name = message.text
    
    users[chat_id]["name"] = name
    
    modify_step(message.chat.id, "confirm_order")
    
    text = "Your order of"
    bot.send_message(chat_id=message.chat.id, text=text)
    display_cart(message.chat.id)
    text = "will be delivered to\n\n{}\n\n{}\n\n{}\n\nPlease confirm your order".format(users[chat_id]["name"], users[chat_id]["address"], users[chat_id]["phone_number"])
    bot.send_message(chat_id=message.chat.id, text=text)
    text = "Due to current limitations, we only accept cash payments. Once you confirm your order, you will be contacted by our delivery agent to arrange payment and delivery."
    
    
    
    reply_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, input_field_placeholder="Select Payment Method", row_width=1)
    reply_markup.add("Cancel Order")
    reply_markup.add("Proceed")
    
    modify_step(message.chat.id, "confirm_order")
    bot.send_message(chat_id=message.chat.id, text=text, reply_markup=reply_markup)
    

@bot.message_handler(func=lambda message: message.text == "Proceed" and step[str(message.chat.id)]["current"] == "confirm_order")
def confirm_order_handler(message):
    text = "Your order is being processed. You will be contacted by our delivery agent shortly."
    
    bot.send_message(chat_id=message.chat.id, text=text)
    display_main_menu(message.chat.id, "What would you like to do next?")


@bot.message_handler(func=lambda m: True)
def default_handler(message):
    text = "Sorry, I didn't understand that command.\n\nPlease select an option from the menu below."
    display_main_menu(message.chat.id, text)


bot.infinity_polling()
