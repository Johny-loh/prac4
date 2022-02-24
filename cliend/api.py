import requests

URL = 'http://127.0.0.1:5000'


def connect(name: str):
    return requests.post(URL + '/connect', json={'name': name})


def start():
    return requests.post(URL + '/start')


def info():
    return requests.get(URL + '/info').json()


def buy_raw(amount: int, price: int):
    return requests.post(URL + '/buy_raw', json={'amount': amount, 'price': price})


def sell_planes(amount: int, price: int):
    return requests.post(URL + '/sell_planes', json={'amount': amount, 'price': price})


def produce(amount: int):
    return requests.post(URL + '/produce', json={'amount': amount})


def build():
    return requests.post(URL + '/build')


def finish():
    return requests.post(URL + '/finish')
