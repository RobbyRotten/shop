"""Тестовый скрипт для отправки запросов
"""
import requests
import json


base = 'http://127.0.0.1:8000/'

data = {"user_id": 1, "data": [{"book_id": 3, "shop_id": 2, "quantity": 3}, {"book_id": 4, "shop_id": 1, "quantity": 1}]}
data1 = json.dumps(data)
response1 = requests.post(base + 'new/', data=data1)
response2 = requests.get(base + 'order/1')

print(response1.json())
print(response2.json())