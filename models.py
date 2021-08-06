"""Скрипт для создания БД и заполнения ее произвольными данными
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Table, Date, create_engine
from sqlalchemy.orm import relationship, backref, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from os import getcwd, remove
from os.path import isfile
import datetime


# При наличии файла БД с таким названием удаляем его, т.к. база создается заново
path = '{}/shop.db'.format(getcwd())
if isfile(path):
    remove(path)

# Далее описание таблиц и создание БД
path = 'sqlite:///' + path
engine = create_engine(path, echo=True)

Base = declarative_base()

class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True)
    last_name = Column(String)
    first_name = Column(String)
    email = Column(String)

    def __init__(self, user_id: int, lname: str, fname: str, mail: str):
        self.user_id = user_id
        self.last_name = lname
        self.first_name = fname
        self.email = mail

class Order(Base):
    __tablename__ = "order"
    order_id = Column(Integer, primary_key=True)
    reg_date = Column(Date)
    user_id = Column(Integer, ForeignKey('user.user_id'))

    def __init__(self, order_id: int, reg_date: datetime.date, user_id: int):
        self.order_id = order_id
        self.reg_date = reg_date
        self.user_id = user_id

class OrderItem(Base):
    __tablename__ = "order_item"
    order_item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('order.order_id'))
    book_id = Column(Integer, ForeignKey('book.book_id')) 
    shop_id = Column(Integer, ForeignKey('shop.shop_id'))   
    quantity = Column(Integer)

    def __init__(self, order_item_id: int, order_id: int, book_id: int, shop_id: int, quantity: int):
        self.order_item_id = order_item_id
        self.order_id = order_id
        self.book_id = book_id
        self.shop_id = shop_id 
        self.quantity = quantity 
    
class Book(Base):
    __tablename__ = "book"
    book_id = Column(Integer, primary_key=True)
    book_name = Column(String)
    author = Column(String)
    release_date = Column(Date)

    def __init__(self, book_id: int, name: str, author: str, release_date: datetime.date):
        self.book_id = book_id 
        self.book_name = name 
        self.author = author 
        self.release_date = release_date

class Shop(Base):
    __tablename__ = "shop"
    shop_id = Column(Integer, primary_key=True)
    shop_name = Column(String)
    address = Column(String)

    def __init__(self, shop_id: int, name: str, address: str):
        self.shop_id = shop_id 
        self.shop_name = name 
        self.address = address

Base.metadata.create_all(engine)

# Вставка данных
Session = sessionmaker(bind=engine)
sess = Session()
sess.add_all([User(1, 'Dorian', 'John', 'dr.acula@scrubs.com'),
            User(2, 'Kelso', 'Robert', 'BobKelso@scrubs.com'),
            Order(1, datetime.date.fromisoformat('2021-01-01'), 1),
            Order(2, datetime.date.fromisoformat('2021-07-07'), 2),
            Order(3, datetime.date.fromisoformat('2021-08-04'), 1),
            Order(4, datetime.date.fromisoformat('2021-08-04'), 2),
            Book(1, 'War and peace', 'L. Tolstoy', datetime.date.fromisoformat('2020-01-01')),
            Book(2, 'Atlas shrugged', 'A. Rand', datetime.date.fromisoformat('2020-07-07')),
            Book(3, 'The Lord of the rings', 'J. R. R. Tolkien', datetime.date.fromisoformat('2019-06-12')),
            Book(4, 'The adventures of Sherlock Holmes', 'A. K. Doyle', datetime.date.fromisoformat('2018-05-22')),
            Shop(1, 'BookShop#1', 'NY'),
            Shop(2, 'Books', 'LA'),
            OrderItem(1, 1, 1, 1, 1),
            OrderItem(2, 2, 2, 2, 2),
            OrderItem(3, 3, 1, 2, 3),
            OrderItem(4, 4, 2, 1, 1),
            OrderItem(5, 1, 1, 1, 1),
            OrderItem(6, 2, 2, 2, 2)
])
sess.commit()
sess.close()