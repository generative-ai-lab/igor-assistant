import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime
import base64
import json
from io import BytesIO

# from pydub import AudioSegment

import aiohttp

from aiogram import Router, html
from aiogram.types import Message, Voice, BufferedInputFile
from aiogram.filters import Filter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.methods.send_voice import SendVoice

from bot.bot import bot
from bot.db.models import ChatMessage
from bot.gpt_input import system_prompt
from bot.openai_api import openai_client

from bot.logger import logger


audio_folder = Path(os.getcwd())/'audio'
router = Router(name="contents-router")


class VoiceFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.voice is not None


async def generate_answer(text, user, session, is_text=True):
    user_id = user.id
    user_first_name = user.first_name
    user_last_name = user.last_name
    username = user.username
    
    sql = select(ChatMessage)\
        .filter_by(user_id=user_id)\
        .order_by(ChatMessage.date_time.desc())\
        .limit(9)
    last_messages = await session.execute(sql)
    
    gpt_messages = []
    gpt_messages.append({'role': 'system', 'content': system_prompt})
    for m in last_messages:
        m_ = m._mapping['ChatMessage']
        gpt_messages.append({'role': m_.role, 'content': m_.content})
    
    gpt_messages = [gpt_messages[0]] + gpt_messages[1:][::-1]
    gpt_messages.append({'role': 'user', 'content': text})
    
    session.add(ChatMessage(
        user_id=user_id,
        user_first_name=user_first_name,
        user_last_name=user_last_name,
        username=username,
        role='user', 
        content=text, 
        is_text=is_text, 
        date_time=datetime.now()))
    await session.commit()
    
    compl = await openai_client.chat.completions.create(messages=gpt_messages, model='gpt-4-1106-preview', temperature = 0.3)
    answer = compl.choices[0].message
    answer_text = answer.content.replace('**', '').replace('__', '')
    
    session.add(ChatMessage(
        user_id=user_id, 
        user_first_name=user_first_name,
        user_last_name=user_last_name,
        username=username,
        role=answer.role, 
        content=answer_text, 
        is_text=True, 
        date_time=datetime.now()))
    await session.commit()
    
    return answer_text


# VOICE_GEN_URL = "http://109.248.175.40:11110/gen_voise"

# async def generate_audio(text):
#     async with aiohttp.ClientSession() as session:
#         data = {'text': text}
        
#         async with session.post(VOICE_GEN_URL, json=data) as response:
#             json_data = await response.json()
#             logger.info(json_data)
#             voice_b64 = json_data['voice_b64']
#             voice = base64.b64decode(voice_b64)
    
#             fn = f"{uuid4()}.wav"
#             with open(audio_folder/fn, 'wb') as audio_file:
#                 audio_file.write(voice)
            
#             return fn


# @router.message(VoiceFilter())
# async def handle_voice_message(message: Message, session: AsyncSession):
#     fn = f"{uuid4()}.ogg"
#     file_id = message.voice.file_id
    
#     # Скачивание файла
#     file = await bot.get_file(file_id)
#     file_path = file.file_path

#     await bot.download_file(file_path, audio_folder/fn)
#     binary_audio = open(audio_folder/fn, "rb")
    
#     # Здесь можно добавить логику обработки голосового сообщения
#     # await message.answer("Я получил ваше голосовое сообщение! Формирую ответ.")
    
#     # answer = await transcribes(fn, binary_audio)
    
#     transcript = await openai_client.audio.transcriptions.create(
#         model="whisper-1", 
#         file=binary_audio,
#         response_format='text',
#         language='ru'
#     )
    
#     if transcript is None:
#         await message.answer("Извините, я не смог обработать ваше сообщение.")
#         return
    
#     # await message.answer(f"Вы сказали: {transcript}")
    
#     answer = await generate_answer(transcript, message.from_user.id, session, is_text=False)
    
#     audio_fn = await generate_audio(answer)
    
#     audio = AudioSegment.from_file(audio_folder/audio_fn, format="wav")
#     output_buffer = BytesIO()
#     audio.export(output_buffer, format="ogg", codec="libopus")
#     ogg_opus_bytes = output_buffer.getvalue()
#     audio_file = BufferedInputFile(ogg_opus_bytes, filename=audio_fn)
    
#     await message.answer(answer)
#     await SendVoice(chat_id=message.chat.id, voice=audio_file)


@router.message()
async def handle_text(message: Message, session: AsyncSession):
    # Здесь вы можете добавить логику обработки сообщения
    text = message.text
    # await message.answer(f"Вы отправили текст: {text}")
    
    # await message.answer("Я получил ваше сообщение! Формирую ответ.")
    
    answer = "ответ" # await generate_answer(text, message.from_user, session)
    
    # audio_fn = await generate_audio(answer)
    
    # audio = AudioSegment.from_file(audio_folder/audio_fn, format="wav")
    # output_buffer = BytesIO()
    # audio.export(output_buffer, format="ogg", codec="libopus")
    # ogg_opus_bytes = output_buffer.getvalue()
    # audio_file = BufferedInputFile(ogg_opus_bytes, filename=audio_fn)
    
    await message.answer(answer)
    # await SendVoice(chat_id=message.chat.id, voice=audio_file)
    