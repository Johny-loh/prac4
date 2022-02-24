from flask import Flask, request, jsonify

from utils import Game

app = Flask(__name__)

game = Game()


#
# Коды:
#
# 200 - OK
# 201 - Лобби создано (тот, кто получил этот статус — хост)
# 400 - Неправильные данные в запросе
# 401 - Не авторизован\недостаточно прав
#

@app.post('/connect')
def connect():
    if game.started:
        return '', 400

    name = request.json['name']
    player = game.add_player(name)

    if game.host is None:
        game.set_host_player(player)
        return '', 201

    return '', 200


@app.post('/start')
def start():
    if game.host.ip != request.remote_addr:
        return '', 401

    game.start()

    return '', 200


@app.get('/info')
def information():
    return jsonify(game.to_dict())


@app.post('/buy_raw')
def buy_raw():
    res = game.buy_raw(request.json['amount'], request.json['price'])

    if not res:
        return '', 400

    return '', 200


@app.post('/sell_planes')
def sell_planes():
    res = game.sell_planes(request.json['amount'], request.json['price'])

    if not res:
        return '', 400

    return '', 200


@app.post('/produce')
def produce():
    res = game.produce(request.json['amount'])

    if not res:
        return '', 400

    return '', 200


@app.post('/build')
def build():
    res = game.build()

    if not res:
        return '', 400

    return '', 200


@app.post('/finish')
def finish():
    game.finish()

    return '', 200


if __name__ == '__main__':
    app.run()
