from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(String, primary_key=True)
    fullname = Column(String)
    phone = Column(String)
    address = Column(String)
    is_admin = Column(Integer)

    def __repr__(self):
        return f"User(uid='{self.id}', fullname='{self.fullname}')"


class Order(Base):
    __tablename__ = 'order'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    items = relationship("OrderItem")
    total_cost = Column(String)
    state = Column(String)  # pending, confirmed, completed, cancelled

    def __repr__(self):
        return f"Order(oid='{self.id}', user='{self.user_id}', cost='{self.total_cost}')"


class OrderItem(Base):
    __tablename__ = 'order_item'
    id = Column(Integer, primary_key=True)
    product = Column(String)
    quantity = Column(Integer)
    price = Column(String)
    order_id = Column(Integer, ForeignKey('order.id'))

    def __repr__(self):
        return f"OrderItem(id='{self.id}', order='{self.order_id}', product='{self.product}', quantity='{self.quantity}')"


class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(String)
    description = Column(String)
    image = Column(String)

    def __repr__(self):
        return f"Product(name='{self.name}', price='{self.price}')"


class Cart(Base):
    __tablename__ = 'cart'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    items = relationship("CartItem")
    total_cost = Column(String)

    def __repr__(self):
        return f"Cart(id='{self.id}', user='{self.user_id}')"


class CartItem(Base):
    __tablename__ = 'cart_item'
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('product.id'))
    quantity = Column(Integer)
    price = Column(String)
    cart_id = Column(Integer, ForeignKey('cart.id'))

    def __repr__(self):
        return f"CartItem(id='{self.id}', cart='{self.cart_id}', product='{self.product_id}', quantity='{self.quantity}')"


class OrderNotificationUser(Base):
    __tablename__ = 'order_notification_user'
    chat_id = Column(Integer, primary_key=True)
