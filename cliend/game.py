import sys
import time
from threading import Thread

from rich.console import Console
from rich.table import Table

from api import *

console = Console()

console.print('[underline blue]KB PUM[/] by [red]Johny[/]')
console.print()

name = console.input('Твоё имя > ')

res = connect(name)
if not res.ok:
    console.print('[red]Выбери другое имя![/]')
    sys.exit(-1)

is_host = res.status_code == 201
host_start = False

if is_host:
    def dummy():
        global host_start

        console.input()
        host_start = True


    t = Thread(target=dummy, daemon=True)
    t.start()

# ждём, пока все присоединятся
while 1 and not host_start:
    console.clear()
    game = info()
    if game['started']:
        break

    console.print('[blue]Ждём всех игроков…[/]')
    console.print('[bold]Твоё имя[/]: [underline]' + name + '[/]')
    console.print()
    console.print('[bold]Игроки:[/]')
    for player in game['players']:
        console.print('- [underline]' + player['name'] + '[/]')

    if is_host:
        console.print()
        console.print('[underline yellow]Чтобы начать игру, нажми [bold]ENTER[/bold]![/]')

    time.sleep(1)

console.clear()
if is_host:
    start()


def input_int(prompt: str = None):
    while 1:
        num = console.input(prompt)

        try:
            return int(num)
        except:
            console.print('[red]Введи число![/]')


month = -1

# главный цикл игры
while 1:
    console.clear()
    game = info()
    if game['ended']:
        console.print('[yellow]Конец игры…')
        sys.exit(0)

    market = game['market']

    table = Table(show_header=True, title='Рынок', header_style="bold magenta")
    table.add_column('Уровень')
    table.add_column('Всего сырья')
    table.add_column('Спрос на самолёты')
    table.add_column('Мин. цена покупки сырья')
    table.add_column('Макс. цена продажи самолёта')

    table.add_row(f"🔥 {market['level']}", f"📦 {market['total_ore']} шт.", f"📊 {market['planes_demand']} шт.",
                  f"📉 {market['minimal_price']} ₿", f"📈 {market['maximal_price']} ₿")

    console.print(table)

    if game['messages']:
        console.rule('Сообщения')

        for message in game['messages'][-7:]:
            console.print(f'- [underline]{message}[/]')

    if month != game['month']:
        console.rule('Действия')

        console.print('1. Купить сырьё 📦')
        console.print('2. Продать самолёты ✈️')
        console.print('3. Изготовить самолёты ✈️')
        console.print('4. Построить завод 🛠️')
        console.print()
        console.print('f. Закончить ход ✅')
        action = console.input('> ')

        success = True
        if action == '1':
            amount = input_int('Количество > ')
            price = input_int('Цена за 1 шт. > ')

            res = buy_raw(amount, price)
            success = res.ok
        elif action == '2':
            amount = input_int('Количество > ')
            price = input_int('Цена за 1 шт. > ')

            res = sell_planes(amount, price)
            success = res.ok
        elif action == '3':
            amount = input_int('Количество > ')

            res = produce(amount)
            success = res.ok
        elif action == '4':
            res = build()
            success = res.ok
        elif action == 'f':
            res = finish()
            month = game['month']

            success = res.ok
        else:
            success = False

        if not success:
            console.print('[red]Что-то не так… Попробуй перепроверить данные[/]')
        else:
            console.print('[green]Всё ОК![/]')

    time.sleep(3)
