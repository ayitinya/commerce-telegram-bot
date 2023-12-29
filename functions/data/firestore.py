# pylint: disable = line-too-long, missing-module-docstring, missing-class-docstring, missing-function-docstring, too-many-arguments, redefined-builtin

import dataclasses
from decimal import Decimal
from typing import Optional, Union, TypeVar

from DatabaseInterface import CartItem, DBInterface, Order, OrderState, User, Product
import firebase_admin

from google.cloud import firestore


T = TypeVar('T')


def not_none(obj: Optional[T]) -> T:
    assert obj is not None
    return obj


class Firestore(DBInterface):
    """
    Implementation of the DBInterface for Firestore
    """

    def __init__(self):
        self.app = firebase_admin.initialize_app()
        self.db = firestore.Client()

    def create_new_user(self, id_: str, display_name: str = "", phone: str = "", address: str = "", is_admin: int = 0):
        """Creates a new user in the database

        Args:
            id_ (str): The user's ID
            display_name (str, optional): The user's display name. Defaults to "".
            phone (str, optional): The user's phone number. Defaults to "".
            address (str, optional): The user's address. Defaults to "".
            is_admin (int, optional): Whether the user is an admin. Defaults to 0.
        """
        self.db.collection("users").document(id_).set({
            "display_name": display_name,
            "phone": phone,
            "address": address,
            "isAdmin": is_admin
        })

    def get_user_by_id(self, id_):

        user = self.db.collection("users").document(id_).get()
        if user.exists:
            return User(id_, **not_none(user.to_dict()))
        return None

    def update_user(self, id_: str, display_name: str = "", phone: str = "", address: str = "", is_admin: int = 0) -> User:
        """Updates a user in the database

        Args:
            id_ (str): The user's ID
            display_name (str, optional): The user's display name. Defaults to "".
            phone (str, optional): The user's phone number. Defaults to "".
            address (str, optional): The user's address. Defaults to "".
            is_admin (int, optional): Whether the user is an admin. Defaults to 0.

        Returns:
            User: The updated user
        """
        self.db.collection("users").document(id_).update({
            "display_name": display_name,
            "phone": phone,
            "address": address,
            "isAdmin": is_admin
        })
        return not_none(self.get_user_by_id(id_))

    def get_users(self) -> list[User]:
        return [User(user.get("id"), **not_none(user.to_dict())) for user in self.db.collection("users").stream()]

    def authenticate_user(self, id_: str) -> User:
        """Sets a user's is_admin to 1

        Args:
            id_ (str): The user's ID

        Returns:
            User: The user
        """
        return self.update_user(id_, is_admin=1)

    def create_product(self, name, price: str, description: str, image: str):
        """Creates a product in the database

        Args:
            name ([type]): The product's name
            price (str): The product's price
            description (str): The product's description
            image (str): The product's image

        Returns:
            Product: The product
        """
        self.db.collection("products").add({
            "name": name,
            "price": price,
            "description": description,
            "image": image
        })

    def get_products(self) -> list[Product]:
        """Gets all products from the database

        Returns:
            dict[str, Product]: A dictionary of products
        """
        return [Product(product.get("id"), **not_none(product.to_dict())) for product in self.db.collection("products").stream()]
    
    def get_products_by_name(self, name: str) -> list[Product]:
        products = self.db.collection("products").where("name", "==", name).stream()
        return [Product(product.get("id"), **not_none(product.to_dict())) for product in products]

    def get_product_by_id(self, id_: str) -> Union[Product, None]:
        product = self.db.collection("products").document(id_).get()
        if product.exists:
            return Product(id_=product.get("id"), **not_none(product.to_dict()))
        return None

    def remove_product(self, id_: str):
        """Removes a product from the database

        Args:
            id_ (str): The product's ID
        """
        self.db.collection("products").document(id_).delete()

    def add_to_cart(self, user_id, product: str, quantity: int, price: Decimal):
        self.db.collection("carts").document(user_id).set({
            "items": [{
                "product_id": product,
                "quantity": quantity,
            }],
        })

    def get_cart_items(self, user_id) -> list[CartItem]:

        cart_ref = self.db.collection("carts").document(user_id).get()

        cart: list[CartItem] = []

        if cart_ref.exists:
            not_none(cart_ref.to_dict())
            cart_dict = not_none(cart_ref.to_dict())
            cart_items = cart_dict["items"]
            for item in cart_items:
                product = self.get_product_by_id(item["product_id"])
                if product is not None:
                    cart.append(
                        CartItem(product=product, quantity=item["quantity"]))

        return cart

    def get_cart(self, user_id) -> dict[str, Union[Decimal, list[CartItem]]]:

        total_cost = Decimal(0.0)
        cart_items = self.get_cart_items(user_id)

        for item in cart_items:
            total_cost += Decimal(item.product.price) * item.quantity

        return {
            "total_cost": total_cost,
            "products": cart_items
        }

    def remove_item_from_cart(self, user_id: str, *args: str):
        # this won't work
        for item in args:

            self.db.collection("carts").document(user_id).update(
                {"items": firestore.ArrayRemove([item])})

    def create_order(self, user_id: str, total_cost: Decimal, items: list[CartItem]):
        order_ref = self.db.collection("orders").document()
        order_ref.set({
            "id": order_ref.id,
            "user": dataclasses.asdict(not_none(self.get_user_by_id(user_id))),
            "total_cost": total_cost,
            "state": OrderState.PENDING,
            "items": [{"product": dataclasses.asdict(item.product), "quantity": item.quantity} for item in items],
        })
        return order_ref.id
    
    def get_orders(self, **kwargs) -> list[Order]:
        orders = self.db.collection("orders").stream()
        return [Order(order.get("id"), **not_none(order.to_dict())) for order in orders]

    def get_orders_by_order_state(self, state: OrderState) -> list[Order]:
        orders = self.db.collection("orders").where(
            "state", "==", state).stream()
        return [Order(order.get("id"), **not_none(order.to_dict())) for order in orders]

    def get_order_by_id(self, id_):
        order = self.db.collection("orders").document(id_).get()
        if order.exists:
            return Order(order.get("id"), **not_none(order.to_dict()))
        return None

    def update_order(self, order_id, state):
        self.db.collection("orders").document(
            order_id).update({"state": state})

    def update_product(self, id_: str, **kwargs):
        self.db.collection("products").document(id_).update(kwargs)
