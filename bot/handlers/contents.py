from datetime import datetime

from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import ChatMessage, User
from bot.gpt_input import system_prompt
from bot.openai_api import openai_client

# from pydub import AudioSegment

# audio_folder = Path(os.getcwd())/'audio'

router = Router(name="contents-router")

# class VoiceFilter(Filter):
#     async def __call__(self, message: Message) -> bool:
#         return message.voice is not None

MAX_CONTEXT_WINDOW = 5


async def generate_answer(text, user, session, is_text=True):
    user_id = user.id

    # Check if user exists and get or create the user
    existing_user = await session.execute(select(User).filter_by(user_id=user_id))
    existing_user = existing_user.scalars().first()

    if not existing_user:
        # Create a new user record if it doesn't exist
        new_user = User(
            user_id=user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            context_window=0
        )
        session.add(new_user)
        await session.commit()
        context_window = 0
    else:
        context_window = min(existing_user.context_window, MAX_CONTEXT_WINDOW)

    print(f'{context_window=}')

    sql = select(ChatMessage) \
        .filter_by(user_id=user_id) \
        .order_by(ChatMessage.date_time.desc()) \
        .limit(context_window * 2)
    # print(f"limit is {context_window * 2}")
    # print(f"sql query that sends as context{sql}")
    last_messages = await session.execute(sql)

    gpt_context = [{'role': m.role, 'content': m.content} for m in last_messages.scalars()][::-1]

    gpt_context.append({'role': 'user', 'content': text})
    print(f"gpt context messages {gpt_context}")

    session.add(ChatMessage(
        user_id=user_id,
        role='user',
        content=text,
        is_text=is_text,
        date_time=datetime.now()))
    await session.commit()


    compl = await openai_client.chat.completions.create(
        messages=gpt_context, model="gpt-4-turbo-preview", temperature=0.3)
    answer = compl.choices[0].message
    answer_text = answer.content.replace('**', '').replace('__', '')

    session.add(ChatMessage(
        user_id=user_id,
        role=answer.role,
        content=answer_text,
        is_text=True,
        date_time=datetime.now()))
    await session.commit()


    existing_user.context_window = context_window + 1
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

    answer = await generate_answer(text, message.from_user, session)

    # audio_fn = await generate_audio(answer)

    # audio = AudioSegment.from_file(audio_folder/audio_fn, format="wav")
    # output_buffer = BytesIO()
    # audio.export(output_buffer, format="ogg", codec="libopus")
    # ogg_opus_bytes = output_buffer.getvalue()
    # audio_file = BufferedInputFile(ogg_opus_bytes, filename=audio_fn)

    await message.answer(answer)
    # await SendVoice(chat_id=message.chat.id, voice=audio_file)
