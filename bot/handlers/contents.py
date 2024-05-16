import asyncio
from datetime import datetime
from typing import List
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputFile
from aiogram.types.input_media_document import InputMediaDocument
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.filters.state import State, StatesGroup
from bot.bot import bot
from aiogram.filters.text import Text
from bot.db.models import ChatMessage, User, ImagePrompt
from bot.openai_api import openai_client
from bot.static_text import greeting, image_mode, urls_mock, greeting_first, home_page
from bot.keyboards import (choose_generation_options_new, dialog_keyboard,
                           choose_after_generation_options, keyboard_main_menu)

router = Router(name="contents-router")


class UserState(StatesGroup):
    DialogMode = State()
    ImageGenerationMode = State()


MAX_CONTEXT_WINDOW = 5
photo_urls = []


async def generate_answer(text, user, session, image_urls=None):
    user_id = user.id

    existing_user = await session.execute(select(User).filter_by(user_id=user_id))
    existing_user = existing_user.scalars().first()

    context_window = min(existing_user.context_window, MAX_CONTEXT_WINDOW)

    print(f'{context_window=}')

    sql = select(ChatMessage) \
        .filter_by(user_id=user_id) \
        .order_by(ChatMessage.date_time.desc()) \
        .limit(context_window * 2)
    last_messages = await session.execute(sql)

    gpt_context = []
    for message in last_messages.scalars():
        message_content = [{"type": "text", "text": message.content}]
        if message.image_urls:
            for url in message.image_urls:
                message_content.append({"type": "image_url", "image_url": {"url": url}})
        gpt_context.append({"role": message.role, "content": message_content})
    gpt_context = gpt_context[::-1]
    # Add the current user message
    user_message_content = [{"type": "text", "text": text}]
    if image_urls:
        for url in image_urls:
            user_message_content.append({"type": "image_url", "image_url": {"url": url}})
    gpt_context.append({"role": "user", "content": user_message_content})

    print(f"gpt context messages {gpt_context}")

    session.add(ChatMessage(
        user_id=user_id,
        role='user',
        content=text,
        image_urls=image_urls,
        date_time=datetime.now()))
    await session.commit()

    compl = await openai_client.chat.completions.create(
        messages=gpt_context, model="gpt-4o", temperature=0.3, max_tokens=1000)
    answer = compl.choices[0].message
    answer_text = answer.content.replace('**', '').replace('__', '')

    session.add(ChatMessage(
        user_id=user_id,
        role=answer.role,
        content=answer_text,
        date_time=datetime.now()))
    await session.commit()

    existing_user.context_window = context_window + 1
    await session.commit()

    return answer_text


async def generate_image_url(image_prompt, size, quality):

    response = await openai_client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size=size,
        quality=quality,
        n=1,
    )
    return response.data[0].url


@router.callback_query(lambda c: c.data == 'dialog')
async def start_dialog(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    await state.set_state(UserState.DialogMode)
    await callback_query.answer("Режим ассистента")
    await bot.send_message(callback_query.from_user.id, greeting)


@router.callback_query(lambda c: c.data == 'image')
async def generate_image(callback_query: types.CallbackQuery, state: FSMContext):
    # delete the previous bot message
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    await state.set_state(UserState.ImageGenerationMode)
    await callback_query.answer("Режим генерации изображений активирован")
    await bot.send_message(callback_query.from_user.id, image_mode, reply_markup=choose_generation_options_new())


@router.callback_query(lambda c: c.data.startswith("quality:"))
async def choose_quality(callback_query: types.CallbackQuery, state: FSMContext):
    new_quality = callback_query.data.split(':')[1]
    user_data = await state.get_data()
    size = user_data.get("size", "1024x1024")

    await state.update_data(quality=new_quality)
    await callback_query.answer("Качество выбрано!")

    await bot.edit_message_reply_markup(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=choose_generation_options_new(quality=new_quality, size=size)
    )


@router.callback_query(lambda c: c.data.startswith("size:"))
async def choose_size(callback_query: types.CallbackQuery, state: FSMContext):
    new_size = callback_query.data.split(':')[1]
    user_data = await state.get_data()
    quality = user_data.get("quality", "standard")

    await state.update_data(size=new_size)
    await callback_query.answer("Разрешение выбрано!")

    await bot.edit_message_reply_markup(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=choose_generation_options_new(quality=quality, size=new_size)
    )


@router.callback_query(lambda c: c.data == 'home')
async def go_home(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback_query.answer("Возвращаемся в главное меню")
    await bot.send_message(chat_id=callback_query.from_user.id,
                           text=home_page,
                           reply_markup=keyboard_main_menu()
                           )


@router.callback_query(lambda c: c.data == 'generate_again')
async def generate_again(callback_query: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    user_data = await state.get_data()
    text = user_data.get("image_prompt")
    quality = user_data.get("quality", "standard")
    size = user_data.get("size", "1024x1024")

    if text:
        # Regenerate the image using the saved prompt and parameters
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text=f"Перегенерируем ваш запрос – {text} "
                 f"\nС параметрами: \nкачество – {quality} \nразмер изображения – {size}"
        )
        image_urls = [await generate_image_url(image_prompt=text,
                                               size=size,
                                               quality=quality,
                                               ) for _ in range(4)]
        # write urls in imgaeprompt table
        for url in image_urls:
            session.add(ImagePrompt(
                user_id=callback_query.from_user.id,
                image_url=url,
                text_prompt=text,
            ))
            await session.commit()

        await bot.send_media_group(
            chat_id=callback_query.from_user.id,
            media=[InputMediaDocument(media=url) for url in image_urls]
        )
        await bot.send_message(
            chat_id=callback_query.from_user.id,
            text="Выберите опцию после генерации",
            reply_markup=choose_after_generation_options()
        )
    else:
        await callback_query.answer("Не найден предыдущий запрос на генерацию изображения")


@router.message(Text(text="🔁Сбросить диалог с ботом"))
async def reset_dialog(message: Message, session: AsyncSession):
    user_id = message.from_user.id

    query = select(User).filter_by(user_id=user_id)
    result = await session.execute(query)
    user = result.scalars().first()

    if user:
        user.context_window = 0
        await session.commit()
        await message.answer("Диалог сброшен")
    else:
        await message.answer(text="У вас нет существующего контекста диалога для сброса.",
                             reply_markup=keyboard_main_menu()
                             )


@router.message(Text(text="🏠Главное меню"))
async def go_to_main_menu(message: Message, state: FSMContext, session: AsyncSession):
    user_id = message.from_user.id

    query = select(User).filter_by(user_id=user_id)
    result = await session.execute(query)
    user = result.scalars().first()

    if user:
        user.context_window = 0
        await session.commit()
    await state.clear()
    await message.answer(text=home_page,
                         reply_markup=keyboard_main_menu()
                         )


async def collect_photo_urls(message: Message):
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
    photo_urls.append(file_url)



#async foo that will execute after 5 sec it will clear photo_urls list
async def clear_photo_urls():
    await asyncio.sleep(2)
    photo_urls.clear()


@router.message()
async def handle_text(message: Message, session: AsyncSession, state: FSMContext):
    user_data = await state.get_data()
    # remebmer that message.text is the text that user sends for repeating generation
    if await state.get_state() == UserState.DialogMode.state:
        if message.caption:
            await collect_photo_urls(message)
            await asyncio.sleep(1)
            result = await generate_answer(
                text=message.caption,
                user=message.from_user,
                session=session,
                image_urls=photo_urls)
            await bot.send_message(chat_id=message.chat.id, text=result)
            await clear_photo_urls()
        elif message.text:
            if photo_urls is None:
                text = message.text
                answer = await generate_answer(
                    text=text,
                    user=message.from_user,
                    session=session
                )
                await message.answer(text=answer,reply_markup=dialog_keyboard())
            else:
                result = await generate_answer(
                    text=message.text,
                    user=message.from_user,
                    session=session,
                    image_urls=photo_urls)
                await bot.send_message(chat_id=message.chat.id, text=result)
                await clear_photo_urls()
        else:
            await collect_photo_urls(message)
    elif await state.get_state() == UserState.ImageGenerationMode.state:
        text = message.text
        quality = user_data.get("quality", "standard")
        size = user_data.get("size", "1024x1024")
        await message.answer(f"Генерируем ваш запрос – {text} "
                             f"\nС параметрами: \nкачество – {quality}\nразмер изображения – {size}")
        dalle_urls = [await generate_image_url(image_prompt=text,
                                               size=size,
                                               quality=quality,
                                               ) for _ in range(4)]
        for url in dalle_urls:
            session.add(ImagePrompt(
                user_id=message.from_user.id,
                image_url=url,
                text_prompt=text,
            ))
            await session.commit()

        await bot.send_media_group(chat_id=message.chat.id, media=[InputMediaDocument(media=url) for url in dalle_urls])
        await bot.send_message(message.chat.id,
                               text="Выберите опцию после генерации:",
                               reply_markup=choose_after_generation_options()
                               )
        await state.update_data(image_prompt=text, quality=quality, size=size)
    else:
        await message.answer("Выберете режим работы")
