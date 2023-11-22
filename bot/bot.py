from aiogram import Bot

from bot.config_reader import config


bot = Bot(config.bot_token.get_secret_value(), parse_mode="HTML")