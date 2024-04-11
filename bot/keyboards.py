from random import randint

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def keyboard_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥Режим диалога", callback_data="dialog")
            ],
            [
                InlineKeyboardButton(text="🖼️Генератор изображений", callback_data="image")
            ]
        ]
    )


def choose_generation_options_new(quality="standard", size="1024x1024"):
    quality_hd = (" ✅" if quality == "hd" else "") + "HD"
    quality_standard = (" ✅" if quality == "standard" else "") + "Standard"

    size_1024x1024 = (" ✅" if size == "1024x1024" else "") + "1024x1024"
    size_1024x1792 = (" ✅" if size == "1024x1792" else "") + "1024x1792"
    size_1792x1024 = (" ✅" if size == "1792x1024" else "") + "1792x1024"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=quality_hd, callback_data="quality:hd"),
                InlineKeyboardButton(text=quality_standard, callback_data="quality:standard"),
            ],
            [
                InlineKeyboardButton(text=size_1024x1024, callback_data="size:1024x1024"),
                InlineKeyboardButton(text=size_1024x1792, callback_data="size:1024x1792"),
                InlineKeyboardButton(text=size_1792x1024, callback_data="size:1792x1024"),
            ]
        ]
    )


def choose_after_generation_options():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔁Перегенерировать", callback_data="generate_again")
                ],
            [
                InlineKeyboardButton(text="✏️Новый запрос", callback_data="image"),
                ],
            [
                InlineKeyboardButton(text="🏠Вернуться в меню", callback_data="home")
            ]
        ]
    )


def dialog_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏠Главное меню")
                ],
            [
                KeyboardButton(text="🔁Сбросить диалог с ботом")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )