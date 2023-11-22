import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import io

from aiogram import Router, html
from aiogram.types import Message, Voice
from aiogram.filters import Filter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.bot import bot
from bot.db.models import ChatMessage
from bot.gpt_input import system_prompt
from bot.openai_api import openai_client, transcribes


audio_folder = Path(os.getcwd())/'audio'
router = Router(name="contents-router")


class VoiceFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.voice is not None


@router.message(VoiceFilter())
async def handle_voice_message(message: Message, session: AsyncSession):
    fn = f"{uuid4()}.ogg"
    file_id = message.voice.file_id
    
    # Скачивание файла
    file = await bot.get_file(file_id)
    file_path = file.file_path

    binary_audio = await bot.download_file(file_path)
    
    # Здесь можно добавить логику обработки голосового сообщения
    await message.answer("Я получил ваше голосовое сообщение!")
    
    answer = await transcribes(fn, binary_audio)
    if answer is None:
        await message.answer("Извините, я не смог обработать ваше сообщение.")
    else:
        await message.answer(f"Вы сказали: {answer}")


@router.message()
async def handle_text(message: Message, session: AsyncSession):
    # Здесь вы можете добавить логику обработки сообщения
    text = message.text
    # await message.answer(f"Вы отправили текст: {text}")
    
    sql = select(ChatMessage).filter_by(user_id=message.from_user.id).order_by(ChatMessage.date_time.desc()).limit(9)
    # sql = select(ChatMessage)
    last_messages = await session.execute(sql)
    
    gpt_messages = []
    gpt_messages.append({'role': 'system', 'content': system_prompt})
    for m in last_messages:
        m_ = m._mapping['ChatMessage']
        gpt_messages.append({'role': m_.role, 'content': m_.content})
    
    gpt_messages = [gpt_messages[0]] + gpt_messages[1:][::-1]
    gpt_messages.append({'role': 'user', 'content': text})
    
    session.add(ChatMessage(user_id=message.from_user.id, role='user', content=text, date_time=datetime.now()))
    await session.commit()
    
    compl = await openai_client.chat.completions.create(messages=gpt_messages, model='gpt-4-1106-preview')
    answer = compl.choices[0].message
    
    session.add(ChatMessage(user_id=message.from_user.id, role=answer.role, content=answer.content, date_time=datetime.now()))
    await session.commit()
    
    await message.answer(answer.content)
    