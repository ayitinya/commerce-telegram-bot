"""Database module for the bot."""

import decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import CartItem, Order, OrderItem, OrderNotificationUser, User, Product, Cart
from media_handler import delete_image


class DB:
    """Database class for the bot"""

    def __init__(self, db_name="db.sqlite3", echo=False, future=True):
        """

        Args:
            db_name (str, optional): Name of the database file to use for sqlite. Defaults to "db.sqlite3".
            echo (bool, optional): Log database activity to terminal. Defaults to False.
            future (bool, optional): See https://docs.sqlalchemy.org/en/14/core/future.html. Defaults to True.
        """
        self.engine = create_engine(
            f'sqlite:///{db_name}', echo=echo, future=future)
        self.conn = self.engine.connect()
        self.session = Session(self.engine)

    def create(self):
        """Creates the database tables
        """
        from models import Base
        Base.metadata.create_all(self.engine)

    def new_user(self, id, fullname="", phone="", address="", is_admin=0):
        """Creates a new user

        Args:
            id (_type_): ID of the user, usually their telegram ID
            fullname (str, optional): Defaults to "".
            phone (str, optional): Defaults to "".
            address (str, optional): Defaults to "".
            is_admin (int, optional): Defaults to 0.

        Raises:
            Exception: Exception raised by SQLAlchemy when user creation fails

        Returns:
            User: The newly created user
        """
        with self.session:
            try:
                user = User(id=id, fullname=fullname,
                            phone=phone, address=address, is_admin=is_admin)
            except Exception as e:
                raise Exception(e)
            cart = Cart(user_id=id, total_cost=str(decimal.Decimal(0)))
            self.session.add(cart)
            self.session.add(user)
            self.session.commit()
            return user

    def get_user(self, id):
        return self.session.query(User).filter_by(id=id).first()

    def set_user_as_admin(self, id):
        with self.session:
            user = self.session.query(User).filter_by(id=id).first()
            user.is_admin = 1
            self.session.commit()
            return user

    def update_user(self, id, fullname="", phone="", address="", is_admin=0):
        with self.session as session:
            user = session.query(User).filter_by(id=id).first()
            user.fullname = fullname if fullname != "" else user.fullname
            user.phone = phone if phone != "" else user.phone
            user.address = address if address != "" else user.address
            user.is_admin = is_admin if is_admin != user.is_admin else user.is_admin
            session.expire_on_commit = False
            session.commit()
            return user

    def get_users(self):
        users = self.session.query(User).all()
        return {user.id: {"fullname": user.fullname, "phone": user.phone, "address": user.address,
                          "is_admin": user.is_admin} for user in users}

    def new_product(self, name, price, description, image):
        with self.session:
            product = Product(name=name, price=price,
                              description=description, image=image)
            self.session.add(product)
            self.session.commit()
            return product

    def get_products(self):
        products = self.session.query(Product).all()
        return {product.name: {"price": product.price, "description": product.description, "image": product.image} for
                product in products}

    def get_product_by_id(self, id):
        product = self.session.query(Product).filter_by(id=id).first()
        return {"name": product.name, "price": product.price, "description": product.description,
                "image": product.image}

    def remove_product(self, id):
        with self.session:
            product = self.session.query(Product).filter_by(id=id).first()
            delete_image(product.name)
            self.session.delete(product)
            self.session.commit()

    def get_cart_items(self, user_id):
        cart = self.session.query(Cart).filter_by(user_id=user_id).first()
        items = self.session.query(CartItem).filter_by(cart_id=cart.id).all()
        print()
        return [
            {"name": self.get_product_by_id(item.product_id)['name'], "price": item.price, "quantity": item.quantity}
            for item in items]

    def add_to_cart(self, user_id, product, quantity, price):
        with self.session:
            cart = self.session.query(Cart).filter_by(user_id=user_id).first()
            product = self.session.query(
                Product).filter_by(name=product).first()
            cart.total_cost = str((decimal.Decimal(price) * int(quantity)) + (
                decimal.Decimal(cart.total_cost) if cart.total_cost else decimal.Decimal(0)))
            cart_item = CartItem(
                product_id=product.id, quantity=quantity, price=str(price), cart_id=cart.id)
            self.session.add(cart_item)
            self.session.commit()

    def get_cart(self, user_id):
        cart = self.session.query(Cart).filter_by(user_id=user_id).first()
        cart_items = self.session.query(
            CartItem).filter_by(cart_id=cart.id).all()
        products = []
        for product in cart_items:
            products.append(self.session.query(
                Product).filter_by(id=product.product_id).first())

        return {
            "total_cost": cart.total_cost,
            "products": [
                {'product': self.session.query(Product).filter_by(id=product.product_id).first().name,
                 'quantity': product.quantity, 'price': product.price, 'id': product.id} for product in cart_items
            ]
        }

    def remove_item_from_cart(self, user_id, *args):
        with self.session as session:
            cart = session.query(Cart).filter_by(user_id=user_id).first()
            for item in args:
                item = session.query(CartItem).filter_by(id=item).first()
                cart.total_cost = str(
                    decimal.Decimal(cart.total_cost) - (decimal.Decimal(item.price) * int(item.quantity)))
                session.delete(item)
            session.commit()
            return True

    def get_orders(self, **kwargs):
        orders = self.session.query(Order).filter_by(**kwargs).all()
        return {
            order.id: {"user_id": order.user_id, "total_cost": order.total_cost, "state": order.state, "items": [
                {'product': item.product, 'price': item.price,
                 'quantity': item.quantity}
                for item in self.session.query(OrderItem).filter_by(order_id=order.id).all()]}
            for order in orders
        }

    def get_order(self, id):
        order = self.session.query(Order).filter_by(id=id).first()
        user = self.session.query(User).filter_by(id=order.user_id).first()
        return {
            "user_id": order.user_id,
            "fullname": user.fullname,
            "phone": user.phone,
            "address": user.address,
            "total_cost": order.total_cost,
            "state": order.state,
            "items": [
                {'product': item.product, 'price': item.price,
                 'quantity': item.quantity}
                for item in self.session.query(OrderItem).filter_by(order_id=order.id).all()
            ]
        }

    def new_order(self, user_id, total_cost, items):
        def save_order():
            with self.session as session:
                order = Order(user_id=user_id,
                              total_cost=total_cost, state="pending")
                session.add(order)
                session.commit()
                return order.id

        order_id = save_order()
        with self.session as session:
            for item in items:
                order_item = OrderItem(
                    product=item['name'], price=item['price'], quantity=item['quantity'], order_id=order_id)
                session.add(order_item)
            session.commit()

        return order_id

    def activate_notifications(self, user_id):
        with self.session as session:
            if session.query(OrderNotificationUser).filter_by(chat_id=user_id).first():
                return False
            session.add(OrderNotificationUser(chat_id=user_id))
            session.commit()

    def update_order(self, order_id, state):
        with self.session as session:
            order = session.query(Order).filter_by(id=order_id).first()
            order.state = state
            session.commit()

    def deactivate_notifications(self, id):
        with self.session as session:
            session.query(OrderNotificationUser).filter_by(chat_id=id).delete()
            session.commit()

    def get_notification_users(self):
        return [user.chat_id for user in self.session.query(OrderNotificationUser).all()]


if __name__ == "__main__":
    db = DB("test.sqlite", echo=True)
    db.create()
    id = 234567890

    if db.get_user(id) is None:
        db.new_user(id, "John Doe", "1234567890", "123 Main St")
        print("User created")
    else:
        print("User already exists")

    db.activate_notifications(id)
    print(db.get_notification_users())

    # print(db.get_order_items(1))
    # db.new_product("product1", 50, "product1 description", "product1.jpg")
    # try:
    #     db.new_order(234567890, 100, [{"name": "product1", "price": 50, "quantity": 2}, {
    #                  "name": "product2", "price": 50, "quantity": 1}])
    # except Exception as e:
    #     print(e)

    # print(db.get_orders(state="pending"))

    # print(db.get_order(1))
    # print(db.session.query(OrderItem).all())
