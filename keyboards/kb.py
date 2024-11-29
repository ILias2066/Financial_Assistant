from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='10'),
            KeyboardButton(text='20'),
            KeyboardButton(text='30'),
            KeyboardButton(text='40'),
            KeyboardButton(text='50'),
        ],
    ],
    resize_keyboard=True)