from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InaccessibleMessage
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession
from mss import mss
import numpy as np
import asyncio, cv2
import json
import pyautogui
import os


USER_ID = None
work = True
need_find = False
templates_list = os.listdir('templates')
templates = list()
bot = None
dp = Dispatcher()
w, h, max_loc = 1920, 1080, (0, 0) #Ширина Высота и лучшие координаты найденого шаблона
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='/on')],
        [KeyboardButton(text='/off')],
        [KeyboardButton(text='/status')],
        [KeyboardButton(text='/stop')],
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)
keyboard_agry = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Принять игру', callback_data='agry')]
    ]
)


@dp.callback_query() #Отслеживаем нужные события
async def callback(callback : CallbackQuery):
    if (callback.data == 'agry'):
        pyautogui.click(max_loc[0] + w // 2, max_loc[1] + h // 2)
        if (isinstance(callback.message, InaccessibleMessage) or callback.message == None):
            return
        await callback.message.edit_text("✅ Игра принята!")
    await callback.answer()


@dp.message(Command('start')) #Обработчик start
async def cmd_start(message: Message):
    global USER_ID
    file = dict()
    with open('needs.json', 'r') as file_json:
        file = json.load(file_json)
    if message.from_user:
        USER_ID = message.from_user.id
        file['USER_ID'] = message.from_user.id
    with open('needs.json', 'w') as file_json:
        json.dump(file, file_json, indent=2)
    await send_message(text="Бот работает")


@dp.message(Command('help')) #Обработчик help
async def cmd_help(message: Message):
    text = '''
Краткий чек лист по командам бота
/start - Сохраняет чат айди
/help - Выдает подсказку по командам
/on - Включает поиск кнопки
/off - Выключает поиск кнопки
/status - Показывает статус поиска
/stop - Выключает бота
    '''
    await send_message(text=text)


@dp.message(Command('on')) #Обработчик on
async def cmd_on(message : Message):
    global need_find, work
    if (USER_ID == None or bot == None):
        print("Ошибка инициализации")
        return
    need_find = True
    await send_message(text="Бот ищет кнопку")


@dp.message(Command('off')) #Обработчик off
async def cmd_off(message : Message):
    global need_find, work
    if (USER_ID == None or bot == None):
        print("Ошибка инициализации")
        return
    need_find = False
    await bot.send_message(chat_id=USER_ID, text="Бот больше не ищет кнопку")


@dp.message(Command('status')) #Обработчик status
async def cmd_status(message: Message):
    global USER_ID
    if (need_find):
        await send_message("✅ Бот ищет кнопку",)
    else:
        await send_message("❌ Бот не ищет кнопку")


@dp.message(Command('stop')) #Обработчик stop
async def cmd_stop(message : Message):
    global need_find, work
    if (USER_ID == None or bot == None):
        print("Ошибка инициализации")
        return
    need_find = False
    work = False
    await send_message(text="Бот выключен")
    await dp.stop_polling()
    await bot.close()


async def send_message(text : str): #Отправить сообщение с нужной клавиатурой
    if (USER_ID == None or bot == None):
        print("Ошибка инициализации")
        return
    await bot.send_message(chat_id=USER_ID, text=text, reply_markup=keyboard)


async def check(): #Проверка экрана на присутсвие шаблона
    global work, need_find, w, h, max_loc
    if bot == None or USER_ID == None:
        print("Ошибка инициализации")
        return
    while work:
        if not need_find: #Если не ищем то спим
            await asyncio.sleep(1)
            continue
        with mss() as sct:
            screenshot = sct.grab(sct.monitors[1]) #Делаем скрин первого монитора
            source = np.array(screenshot)
            source = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
            for template in templates: #Бегаем по всем шаблонам
                w, h = template.shape
                result = cv2.matchTemplate(image=source, templ=template, method=cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                if max_val > 0.6:
                    await bot.send_message(chat_id=USER_ID, text="Игра найдена", reply_markup=keyboard_agry)
                    await asyncio.sleep(10)
                    break
                await asyncio.sleep(0.5)
        await asyncio.sleep(2)


async def main():
    global USER_ID, bot, templates

    for name in templates_list: #Добавляем все шаблоны в массив
        templates.append(cv2.imread(f'templates/{name}', cv2.IMREAD_GRAYSCALE))

    print("Бот запущен")
    with open('needs.json', 'r') as file_json:
        file = json.load(file_json)
        USER_ID = file.get('USER_ID')
        if USER_ID == 0:
            USER_ID = None
        TOKEN = file.get('TOKEN')
        PROXY = file.get('PROXY', 'socks5://74.119.147.209:4145')
    session = AiohttpSession(proxy=PROXY)
    bot = Bot(token=TOKEN, session=session)
    await asyncio.gather(
        dp.start_polling(bot),
        send_message(text="Бот прогрузился"),
        check()
    )


if __name__ == "__main__":
    asyncio.run(main())