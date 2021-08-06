"""Скрипт для обработки запросов к приложению
"""

from fastapi import FastAPI, Header
from os import getcwd
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
from pydantic import BaseModel
from typing import List, Dict, Union
import datetime
import logging as log


# Класс для аннотирования параметров в функции add_data()
class Item(BaseModel):
    book_id: int
    shop_id: int
    quantity: int

app = FastAPI()
log.basicConfig(filename="logs.log", level=log.INFO)

# Тестовый обработчик для проверки, что приложение работает
@app.get("/")
async def root():
    return {"info": "application is running"}

# Обработчие get-запросов
@app.get("/{section}/{item_id}")
async def get_data(section: str, item_id: int) -> Dict:
    write_log('i', 'query: {}/{}'.format(section, item_id))
    # Вернуть информацию по запросу
    return {"info": run_query(section, item_id)}

# Обработчик post-запросов
@app.post("/new/")
async def add_data(data: Dict[str, Union[List[Item], int]]) -> Dict:
    write_log('i', 'inserting: {}'.format(data))
    output = add_entries(data)
    # Если в add_entries() не было предупреждений, сообщить об успешном 
    # добавлении данных, в противном случае - сообщить, какие ошибки были
    if output == 'ok':
        return {"info": "successfully inserted"}
    return {"info": output}


# Функция для добавления в БД данных, полученных в post-запросе
def add_entries(data: Dict[str, Union[List[Item], int]]) -> str:
    try:
        # Импорт моделей для создания новых записей
        from models import Order, OrderItem

        # Список для сбора предупреждений
        warnings = []
        # Подключение к БД 
        path = "sqlite:///{}/shop.db".format(getcwd())
        engine = create_engine(path, echo=True)
        Base = automap_base()
        Base.prepare(engine, reflect=True)
        session = Session(engine)
        
        User = Base.classes.user
        Book = Base.classes.book
        Shop = Base.classes.shop

        # Получение последнего значения primary key + 1 для каждой из таблиц, куда пойдет вставка
        last_order_id = session.query(func.max(Order.order_id)).one()[0] + 1
        last_order_item_id = session.query(func.max(OrderItem.order_item_id)).one()[0] + 1

        # Получения спосков действительных user_id, book_id, shop_id для проверки вставляемых данных
        valid_user_ids = [n.user_id for n in session.query(User).all()]
        valid_book_ids = [n.book_id for n in session.query(Book).all()]
        valid_shop_ids = [n.shop_id for n in session.query(Shop).all()]

        saved_order_item_id = last_order_item_id
        # Проверка, есть ли такой пользователь в БД
        if data['user_id'] in valid_user_ids:
            # Если пользователь есть, вставляем данные о его заказе
            session.add(Order(last_order_id, datetime.date.today(), data['user_id']))
            session.commit()
            write_log('i', 'line inserted in Order (id={})'.format(last_order_id))

            for item in data['data']:  
                book_id = item.book_id
                shop_id = item.shop_id
                # Проверка, есть ли такая книга в БД
                if book_id not in valid_book_ids:
                    warnings.append('Invalid book id: {}'.format(book_id))
                # Проверка, есть ли такой магазин в БД
                elif shop_id not in valid_shop_ids:
                    warnings.append('Invalid shop id: {}'.format(shop_id))
                else:
                    # Если все проверки пройдены, вставляем строку позиции заказа в таблицу
                    session.add(OrderItem(last_order_item_id, 
                                        last_order_id, 
                                        item.book_id, 
                                        item.shop_id, 
                                        item.quantity
                                        ))
                    session.commit()
                    # Инкременируем значение primary key для дальнейшей вставки позиций
                    last_order_item_id += 1
                session.close()
                write_log('i', '{} lines inserted in OrderItem (ids {}-{})'.format(last_order_item_id-saved_order_item_id+1,
                                                                                   saved_order_item_id,
                                                                                   last_order_item_id))
        else:
            # Если пользователь недействителен, вставка по нему не производится
            warnings.append('Invalid user id: {}'.format(data['user_id']))
        
        # Если нет предупреждений, возвращаем "ок", в противном случае -
        # возвращаем сообщение, какие ошибки были
        if len(warnings) == 0:
            return 'ok'
        ws = '; '.join(warnings)
        write_log('w', ws)
        return(ws)
    except Exception as e:
        write_log('e', e)
        return [e]

# Функция для получения из БД данных по параметрам из get-запроса
def run_query(section: str, item_id: int) -> List:
    try:
        # Подключене к БД
        path = "sqlite:///{}/shop.db".format(getcwd())
        engine = create_engine(path, echo=True)
        Base = automap_base()
        Base.prepare(engine, reflect=True)

        User = Base.classes.user
        Order = Base.classes.order
        OrderItem = Base.classes.order_item
        Book = Base.classes.book
        Shop = Base.classes.shop

        session = Session(engine)

        # Выбор таблиц, из которых запрашивать данные, в зависимости от section
        # item_id, в зависимости от section, может быть user_id или order_id 
        if section == "users":
            # Вывести информацию о пользователе по user_id
            res = session.query(User).filter_by(user_id=item_id).first()
            session.close()
            return {"user_id": res.user_id,
                    "last_name": res.last_name,
                    "first_name": res.first_name,
                    "email": res.email
                    }
        elif section == "history": 
            # Вывести информацию о заказах пользователя по user_id
            res = session.query(Order).filter_by(user_id=item_id).all()
            session.close()
            out = []
            for row in res:
                out.append({"order_id": row.order_id,
                            "reg_date": row.reg_date,
                            "user_id": row.user_id,
                            })
            return out
        elif section == "order":
            # Вывести подробную информацию о заказе и позициях по order_id
            res = session.query(OrderItem, Book, Shop).filter_by(order_id=item_id).join(Book).join(Shop).all()
            session.close()
            out = []
            for row in res:
                out.append({"order_item_id": row.order_item.order_item_id,
                            "order_id": row.order_item.order_id,                    
                            "book_id" : row.book.book_id,
                            "book_name": row.book.book_name,
                            "author": row.book.author,
                            "release_date": row.book.release_date,
                            "shop_id": row.shop.shop_id,
                            "shop_name": row.shop.shop_name,
                            "address": row.shop.address,
                            "quantity": row.order_item.quantity
                            })
            return out
        write_log('w', 'Wrong section: {}'.format(section))
        # Если параметр section неверный, вернуть сообщение об этом
        return ['Wrong section: {}'.format(section)]
    except Exception as e:
        write_log('e', e)
        return [e]


# Функция для записи в лог сообщений разных типов
def write_log(mode: str, text: str):
    timestamp = datetime.datetime.today().isoformat()
    if mode == 'e':
        log.error('{} ERROR: {}'.format(timestamp, text))
    elif mode == 'w':
        log.info('{} WARNING: {}'.format(timestamp, text))
    elif mode == 'i':
        log.info('{} INFO: {}'.format(timestamp, text))
