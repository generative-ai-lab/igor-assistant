from aiogram import Router, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from sqlalchemy import select
from bot.db.models import ChatMessage, User
from bot.static_text import greeting, new_dialog_start, home_page, greeting_first
from bot.keyboards import keyboard_main_menu
from aiogram.fsm.context import FSMContext
router = Router(name="commands-router")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    """
    Handles /start command
    :param message: Telegram message with "/start" text
    """
    # ads the user to the database
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username

    # Check if user exists and get or create the user
    existing_user = await session.execute(select(User).filter_by(user_id=user_id))
    existing_user = existing_user.scalars().first()

    if not existing_user:
        # Create a new user record if it doesn't exist
        new_user = User(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            context_window=0
        )
        session.add(new_user)
        await session.commit()
    await state.clear()
    await message.answer(greeting_first, reply_markup=keyboard_main_menu())

@router.message(Command("reset"))
async def cmd_start_new(message: Message, session: AsyncSession):
    """
    Handles /start_new command
    :param message: Telegram message with "/start_new" text
    """

    user_id = message.from_user.id

    # Retrieve the User object from the database
    query = select(User).filter_by(user_id=user_id)
    result = await session.execute(query)
    user = result.scalars().first()

    if user:
        # Update the context window to 1
        user.context_window = 0
        await session.commit()
        await message.answer(new_dialog_start)
    else:
        # In case the user is not found in the database
        await message.answer("You do not have an existing dialog context to reset.")


@router.message(Command("home"))
async def cmd_home(message: Message, state: FSMContext):
    #gets you to the home page and show keyboard for the user to choose from dialog options
    keyboard = keyboard_main_menu()
    await state.clear()
    await message.answer(home_page, reply_markup=keyboard)
