import dataclasses
from dataclasses import dataclass
from random import choices
from typing import List

from flask import request

store_ore_cost = 300
store_plane_cost = 500
store_workshop_cost = 1_000


@dataclass()
class Player:
    name: str
    ip: str

    money: int
    workshops: int
    raw: int
    planes: int

    dead: bool

    def __init__(self, name: str, ip: str):
        self.name = name
        self.ip = ip

        self.money = 10000
        self.workshops = 2
        self.raw = 4
        self.planes = 2

        self.dead = False


initial_level = 3
levels = {
    1: {
        'total_ore': lambda p: int(1.0 * p),
        'planes_demand': lambda p: int(3.0 * p),
        'minimal_price': 800,
        'maximal_price': 6500,
        'chances': {
            1: 1 / 3,
            2: 1 / 3,
            3: 1 / 6,
            4: 1 / 12,
            5: 1 / 12
        },
    },
    2: {
        'total_ore': lambda p: int(1.5 * p),
        'planes_demand': lambda p: int(2.5 * p),
        'minimal_price': 650,
        'maximal_price': 6000,
        'chances': {
            1: 1 / 4,
            2: 1 / 3,
            3: 1 / 4,
            4: 1 / 12,
            5: 1 / 12
        },
    },
    3: {
        'total_ore': lambda p: int(2.0 * p),
        'planes_demand': lambda p: int(2.0 * p),
        'minimal_price': 500,
        'maximal_price': 5500,
        'chances': {
            1: 1 / 12,
            2: 1 / 4,
            3: 1 / 3,
            4: 1 / 4,
            5: 1 / 12
        },
    },
    4: {
        'total_ore': lambda p: int(2.5 * p),
        'planes_demand': lambda p: int(1.5 * p),
        'minimal_price': 400,
        'maximal_price': 5000,
        'chances': {
            1: 1 / 12,
            2: 1 / 12,
            3: 1 / 4,
            4: 1 / 3,
            5: 1 / 4
        },
    },
    5: {
        'total_ore': lambda p: int(3.0 * p),
        'planes_demand': lambda p: int(1.0 * p),
        'minimal_price': 300,
        'maximal_price': 4500,
        'chances': {
            1: 1 / 12,
            2: 1 / 12,
            3: 1 / 6,
            4: 1 / 3,
            5: 1 / 3
        },
    },
}


class Market:
    def __init__(self):
        self.level = initial_level
        self.state = levels[self.level]

    def randomize(self):
        self.level = choices(
            list(levels[self.level]['chances'].keys()),
            list(levels[self.level]['chances'].values())
        )[0]
        self.state = levels[self.level]

    def to_dict(self, players):
        return {
            'level': self.level,
            'total_ore': self.state['total_ore'](players),
            'planes_demand': self.state['planes_demand'](players),
            'minimal_price': self.state['minimal_price'],
            'maximal_price': self.state['maximal_price'],
        }


plane_cost = 2_000
WORKSHOP_COST = 5_000


class Game:
    def __init__(self):
        self.started = False
        self.ended = False

        self.month = 0

        self.host: Player = None
        self.players: List[Player] = []
        self.finished_count = 0

        self.raw_requests = []
        self.sell_requests = []

        self.plane_requests = []
        self.workshop_requests = []

        self.market = Market()

        self.messages = []

    def get_alive_players(self):
        players = []
        for player in self.players:
            if not player.dead:
                players.append(player)

        return players

    def get_current_market(self):
        return self.market.to_dict(len(self.get_alive_players()))

    def get_current_player(self):
        for player in self.players:
            if player.ip == request.remote_addr:
                return player

    def add_player(self, name: str):
        player = Player(name, request.remote_addr)
        self.players.append(player)

        return player

    def set_host_player(self, player: Player):
        self.host = player

    def start(self):
        self.started = True

    def buy_raw(self, amount: int, price: int):
        player = self.get_current_player()
        market = self.get_current_market()

        if not (market['minimal_price'] <= price) or not (0 < amount <= market['total_ore']):
            return False

        req = (player, amount, price)
        self.raw_requests.append(req)

        return True

    def sell_planes(self, amount: int, price: int):
        player = self.get_current_player()

        if player.planes < amount or amount == 0 or price <= 0:
            return False

        req = (player, amount, price)
        self.sell_requests.append(req)

        return True

    def produce(self, amount):
        player = self.get_current_player()

        total_cost = amount * plane_cost
        total_raw = amount

        if amount <= 0 or total_raw > player.raw or total_cost > player.money:
            return False

        player.money -= total_cost
        player.raw -= amount

        req = (player, amount)
        self.plane_requests.append(req)

        return True

    def build(self):
        player = self.get_current_player()

        if player.money < WORKSHOP_COST:
            return False

        player.money -= WORKSHOP_COST

        req = (player, 0)  # 0 - процесс постройки завода
        self.workshop_requests.append(req)

        return True

    def finish(self):
        if self.ended:
            return

        self.finished_count += 1

        if self.finished_count != len(self.get_alive_players()):
            return

        self.finished_count = 0

        try:

            self.process_raw_requests()
            self.process_planes_sell()
            self.process_events()
            self.process_market()

            self.build_planes()
            self.build_workshops()

        except:
            pass

        self.month += 1

        self.process_players()

        self.end_if_required()

        if not self.ended:
            self.messages.append(f'Следующий месяц! ({self.month})')

    def process_raw_requests(self):

        market = self.get_current_market()
        amount = market['total_ore']

        while amount > 0 and self.raw_requests:

            for i in range(len(self.raw_requests)):
                self.raw_requests[i] = (self.raw_requests[i][0], self.raw_requests[i][1] if self.raw_requests[i][1] < amount else amount, self.raw_requests[i][2])

            self.raw_requests = sorted(self.raw_requests, 
                                        key=lambda x: x[1] * x[2],
                                        reverse=True)
            self.raw_requests[0][0].raw += self.raw_requests[0][1]
            self.raw_requests[0][0].money -= self.raw_requests[0][1] * self.raw_requests[0][2]
            self.messages.append(
                f'Банк продал {self.raw_requests[0][1]} шт. сырья {self.raw_requests[0][0].name}')

            amount -= self.raw_requests[0][1]
            del self.raw_requests[0]

    def process_planes_sell(self):

        market = self.get_current_market()
        amount = market['planes_demand']

        while amount > 0 and self.sell_requests:

            for i in range(len(self.sell_requests)):
                self.sell_requests[i] = (self.sell_requests[i][0], self.sell_requests[i][1] if self.sell_requests[i][1] < amount else amount, self.sell_requests[i][2])


            self.sell_requests = sorted(self.sell_requests,
                                        key=lambda x: x[1] * x[2])
            self.sell_requests[0][0].planes -= self.sell_requests[0][1]
            self.sell_requests[0][0].money += self.sell_requests[0][1] * self.sell_requests[0][2]
            self.messages.append(
                f'Банк купил {self.raw_requests[0][0].raw} самолётов у {self.raw_requests[0][0].name}')

            amount -= self.sell_requests[0][1]
            del self.sell_requests[0]

    def process_events(self):
        for player in self.players:
            player.money -= player.raw * store_ore_cost
            player.money -= player.planes * store_plane_cost
            player.money -= player.workshops * store_workshop_cost

    def process_market(self):
        level = self.market.level
        self.market.randomize()

        if level != self.market.level:
            self.messages.append(f'Новый уровень рынка: {level} → {self.market.level}')

    def build_planes(self):
        for player, amount in self.plane_requests:
            player.planes += amount

        self.plane_requests.clear()

    def build_workshops(self):
        done = []

        for i, (player, month) in enumerate(self.workshop_requests):
            if month == 4:
                player.workshops += 1
                done.append((player, month))
            else:
                self.workshop_requests[i] = (player, month + 1)

        for item in done:
            self.workshop_requests.remove(item)

    def process_players(self):
        for player in self.players:
            if not player.dead and player.money < 0:
                player.dead = True
                self.messages.append(f'Игрок {player.name} обанкротился!')

    def end_if_required(self):
        if len(self.get_alive_players()) in [0, 1]:
            self.ended = True

            self.messages.append(
                f'Игра окончена… Выиграли: ' + ', '.join(player.name for player in self.get_alive_players()))

    def to_dict(self):
        return {
            'players': [dataclasses.asdict(player) for player in self.players],
            'messages': self.messages,
            'month': self.month,
            'started': self.started,
            'ended': self.ended,
            'market': self.get_current_market()
        }
