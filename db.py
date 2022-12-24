import decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import CartItem, User, Product, Cart


class DB:
    def __init__(self, db_name="db.sqlite3"):
        self.engine = create_engine(
            f'sqlite:///{db_name}', echo=True, future=True)
        self.conn = self.engine.connect()
        self.session = Session(self.engine)

    def create(self):
        from models import Base
        Base.metadata.create_all(self.engine)

    def new_user(self, id, fullname="", phone="", address="", is_admin=0):
        with self.session:
            try:
                user = self.session.query(User).filter_by(id=id).first()
            except:
                raise Exception("User already exists")
            user = User(id=id, fullname=fullname,
                        phone=phone, address=address, is_admin=is_admin)
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
        return {user.id: {"fullname": user.fullname, "phone": user.phone, "address": user.address, "is_admin": user.is_admin} for user in users}

    def new_product(self, name, price, description, image):
        with self.session:
            product = Product(name=name, price=price,
                              description=description, image=image)
            self.session.add(product)
            self.session.commit()
            return product

    def get_products(self):
        products = self.session.query(Product).all()
        return {product.name: {"price": product.price, "description": product.description, "image": product.image} for product in products}

    def remove_product(self, id):
        with self.session:
            product = self.session.query(Product).filter_by(id=id).first()
            self.session.delete(product)
            self.session.commit()
            return True

    def get_cart_items(self, user_id):
        cart = self.session.query(Cart).filter_by(user_id=user_id).first()
        return {"total_cost": cart.total_cost, "items": cart.items}

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
            return True

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
                {'product': self.session.query(Product).filter_by(id=product.product_id).first().name, 'quantity': product.quantity, 'price': product.price, 'id': product.id} for product in cart_items
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


if __name__ == "__main__":
    db = DB("test.sqlite")
    # db.create()
    id = 234567890

    if db.get_user(id) is None:
        db.new_user(id, "John Doe", "1234567890", "123 Main St")
        print("User created")
    else:
        print("User already exists")
