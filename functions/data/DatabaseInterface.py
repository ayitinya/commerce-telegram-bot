"""
This module contains the interface for the database.
"""

from abc import ABC, abstractmethod

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Type, TypedDict


class OrderState(Enum):
    """
    Represents the state of an order

    Attributes:
        PENDING (str): The order is pending
        PROCESSING (str): The order is being processed
        COMPLETED (str): The order has been completed
        CANCELLED (str): The order has been cancelled
    """
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    IN_PROGRESS = "IN_PROGRESS"


@dataclass
class User:
    """
    Represents a user in the system.

    Attributes:
        id_ (str): The unique identifier of the user.
        display_name (str): The display name of the user.
        phone (str): The phone number of the user.
        address (str): The address of the user.
        is_admin (int): Indicates whether the user is an admin (1) or not (0).
    """
    id_: str
    display_name: str
    phone: str
    address: str
    is_admin: int


@dataclass
class Product:
    """
    Represents a product in the database.

    Attributes:
        id_ (str): The unique identifier of the product.
        name (str): The name of the product.
        price (str): The price of the product.
        description (str): The description of the product.
        image (str): The image URL of the product.
        published (bool): Indicates whether the product is published (True) or not (False).
        status (str): The status of the product.
    """
    id_: str
    name: str
    price: str
    description: str
    image: str
    published: bool
    status: str


@dataclass
class CartItem:
    """
    Represents an item in a cart

    Attributes:
        product (Product): The product
        quantity (int): The quantity of the product

    """
    product: Product
    quantity: int


@dataclass
class Cart:
    """
    Represents a shopping cart.

    Attributes:
        id_: The ID of the cart.
        user_id: The ID of the user who owns the cart.
        items: A list of CartItem objects representing the items in the cart.
        total_cost: The total cost of all items in the cart.
    """
    id_: str
    user_id: str
    items: list[CartItem]
    total_cost: str


@dataclass
class OrderItem:
    """
    Represents an item in an order

    Attributes:
        product (Product): The product
        quantity (int): The quantity of the product
        price (str): The price of the product
    """
    id_: str
    product: Product
    quantity: int
    price: str


@dataclass
class Order:
    """
    Represents an order

    Attributes:
        id_ (str): The order's ID
        user_id (str): The user's ID
        total_cost (str): The total cost of the order
        items (list[OrderItem]): The items in the order
        state (OrderState): The order's state
    """
    id_: str
    user: User
    total_cost: Decimal
    items: list[OrderItem]
    state: OrderState


@dataclass
class OrderInProgress:
    """
    Represents an order in progress

    Attributes:
        product (Product): The product being ordered
        quantity (int): The quantity of the product
    """
    product: Product
    quantity: int


@dataclass
class NavigationHistory:
    """
    Represents the navigation history of a user in a commerce application.

    Attributes:
        user_id (str): The ID of the user.
        current_page (str): The current page the user is on.
        breadcrumb (list[str]): The list of previous pages visited by the user.
    """

    user_id: str
    current_page: str
    breadcrumb: list[str]


class DBInterface(ABC):
    """
    Interface for the database
    """

    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_new_user(self, id_: str, display_name: str = "", phone: str = "", address: str = "", is_admin: int = 0):
        """
        Creates a new user in the database.

        Args:
            id_ (str): The unique identifier for the user.
            display_name (str, optional): The display name of the user. Defaults to "".
            phone (str, optional): The phone number of the user. Defaults to "".
            address (str, optional): The address of the user. Defaults to "".
            is_admin (int, optional): Indicates whether the user is an admin (1) or not (0).
            Defaults to 0.
        """
        raise NotImplementedError

    @abstractmethod
    def get_admins(self) -> list[User]:
        """
        Retrieves all admins from the database.

        Returns:
            list[User]: A list of user objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_user_by_id(self, id_: str) -> (User | None):
        """
        Retrieves a user from the database by their ID.

        Args:
            id_ (str): The ID of the user.

        Returns:
            Union[User, None]: The user object, or None if it doesn't exist.
        """
        raise NotImplementedError

    @abstractmethod
    def update_user(self, id_: str, display_name: str = "", phone: str = "", address: str = "", is_admin: int = 0) -> User:
        """
        Updates the information of a user in the database.

        Args:
            id_ (str): The ID of the user.
            display_name (str, optional): The new display name of the user. Defaults to "".
            phone (str, optional): The new phone number of the user. Defaults to "".
            address (str, optional): The new address of the user. Defaults to "".
            is_admin (int, optional): The new admin status of the user (1 for admin, 0 for non-admin). Defaults to 0.

        Returns:
            User: The updated user object.
        """
        raise NotImplementedError

    @abstractmethod
    def get_users(self) -> list[User]:
        """
        Retrieves all users from the database.

        Returns:
            list[User]: A list of user objects.
        """
        raise NotImplementedError

    @abstractmethod
    def authenticate_user(self, id_: str) -> User:
        """
        Authenticates a user by their ID.

        Args:
            id_ (str): The ID of the user.

        Returns:
            User: The authenticated user object.
        """
        raise NotImplementedError

    @abstractmethod
    def create_product(self, name, price: str, description: str, image: str):
        """
        Creates a new product in the database.

        Args:
            name (str): The name of the product.
            price (str): The price of the product.
            description (str): The description of the product.
            image (str): The image URL of the product.
        """
        raise NotImplementedError

    @abstractmethod
    def get_products(self) -> list[Product]:
        """
        Retrieves all products from the database.

        Returns:
            list[Product]: A list of product objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_products_by_name(self, name: str) -> list[Product]:
        """
        Retrieves all products from the database with a specific name.

        Args:
            name (str): The name of the products to retrieve.

        Returns:
            list[Product]: A list of product objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_product_by_id(self, id_: str) -> dict:
        """
        Retrieves a product from the database by its ID.

        Args:
            id_ (str): The ID of the product.

        Returns:
            Union[Product, None]: The product object, or None if it doesn't exist.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_product(self, id_: str):
        """
        Removes a product from the database.

        Args:
            id_ (str): The ID of the product to be removed.
        """
        raise NotImplementedError

    @abstractmethod
    def get_cart_items(self, user_id: str) -> list[CartItem]:
        """
        Retrieves all items in a user's cart.

        Args:
            user_id (str): The ID of the user.

        Returns:
            list[CartItem]: A list of CartItem objects.
        """
        raise NotImplementedError

    @abstractmethod
    def add_to_cart(self, user_id, product: str, quantity: int, price: Decimal):
        """
        Adds a product to a user's cart.

        Args:
            user_id (str): The ID of the user.
            product (str): The ID of the product to be added.
            quantity (int): The quantity of the product.
            price (Decimal): The price of the product.
        """
        raise NotImplementedError

    GetCartReturn = TypedDict(
        "get_cart_return", {"total_cost": Decimal, "products": list[CartItem]})

    @abstractmethod
    def get_cart(self, user_id: str) -> GetCartReturn:
        """
        Retrieves a user's cart.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict[str, Union[Decimal, list[CartItem]]]: A dictionary containing the total cost of the cart and a list of CartItem objects.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_item_from_cart(self, user_id: str, item: CartItem) -> bool:
        """
        Removes an item from a user's cart.

        Args:
            user_id (str): The ID of the user.
            *args (str): The IDs of the items to be removed.

        Returns:
            bool: True if the item(s) were successfully removed, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def get_orders(self, **kwargs: str) -> list[Order]:
        """
        Retrieves all orders from the database.

        Args:
            **kwargs: Additional arguments to filter the orders.

        Returns:
            list[Order]: A list of order objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_orders_by_order_state(self, state: OrderState) -> list[Order]:
        """
        Retrieves all orders from the database with a specific state.

        Args:
            state (OrderState): The state of the orders to retrieve.

        Returns:
            list[Order]: A list of order objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_order_by_id(self, id_: str) -> (Order | None):
        """
        Retrieves an order from the database by its ID.

        Args:
            id_ (str): The ID of the order.

        Returns:
            Order | None: The order object, or None if it doesn't exist.
        """
        raise NotImplementedError

    @abstractmethod
    def create_order(self, user_id: str, total_cost: Decimal, items: list[CartItem]) -> str:
        """
        Creates a new order in the database.

        Args:
            user_id (str): The ID of the user placing the order.
            total_cost (Decimal): The total cost of the order.
            items (list[CartItem]): The items in the order.

        Returns:
            str: The ID of the order.
        """
        raise NotImplementedError

    @abstractmethod
    def update_order(self, order_id: str, state: OrderState):
        """
        Updates the state of an order in the database.

        Args:
            order_id (str): The ID of the order.
            state (OrderState): The new state of the order.
        """
        raise NotImplementedError

    @abstractmethod
    def update_product(self, id_, **kwargs: str):
        """
        Updates the information of a product in the database.

        Args:
            id_ (str): The ID of the product.
            **kwargs: Additional keyword arguments representing the updated fields of the product.
        """
        raise NotImplementedError

    @abstractmethod
    def create_order_in_progress(self, user_id: str, product: Product):
        """
        Creates a new order in progress in the database.

        Args:
            user_id (str): The ID of the user placing the order.
            product (Product): The product being ordered.
        """
        raise NotImplementedError

    @abstractmethod
    def update_order_in_progress(self, user_id: str, quantity: int):
        """
        Updates an order in progress in the database.

        Args:
            user_id (str): The ID of the user placing the order.
            quantity (int): The new quantity of the product being ordered.
        """
        raise NotImplementedError

    @abstractmethod
    def get_order_in_progress(self, user_id: str) -> (OrderInProgress | None):
        """
        Retrieves an order in progress from the database.

        Args:
            user_id (str): The ID of the user placing the order.

        Returns:
            OrderInProgress: The order in progress object.
        """
        raise NotImplementedError

    @abstractmethod
    def remove_order_in_progress(self, user_id: str):
        """
        Removes an order in progress from the database.

        Args:
            user_id (str): The ID of the user placing the order.
        """
        raise NotImplementedError

    @abstractmethod
    def update_user_navigation(self, user_id: str, path: str, reset: bool = False):
        """
        Updates the navigation of a user in the database.

        Args:
            user_id (str): The ID of the user.
            path (str): The new navigation of the user.
            reset (bool)
        """
        raise NotImplementedError

    @abstractmethod
    def get_user_navigation(self, user_id: str) -> NavigationHistory:
        """
        Retrieves the navigation of a user from the database.

        Args:
            user_id (str): The ID of the user.

        Returns:
            NavigationHistory: The navigation history of the user.
        """
        raise NotImplementedError


class DatabaseFactory:
    """
    Factory class for the database.
    """

    def __init__(self, db_type: Type[DBInterface]):
        self.db_type = db_type

    def get_database(self) -> DBInterface:
        """
        Returns an instance of the database.

        Returns:
            DBInterface: An instance of the database.
        """

        return self.db_type()
