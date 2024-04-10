from aiogram import Router, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from sqlalchemy import select
from bot.db.models import ChatMessage, User
from bot.static_text import greeting, new_dialog_start, home_page, greeting_first
from bot.keyboards import keyboard_main_menu

router = Router(name="commands-router")


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handles /start command
    :param message: Telegram message with "/start" text
    """
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
async def cmd_home(message: Message):
    #gets you to the home page and show keyboard for the user to choose from dialog options
    keyboard = keyboard_main_menu()

    await message.answer(home_page, reply_markup=keyboard)






# @router.message(Command("play"))
# async def cmd_play(message: Message, session: AsyncSession):
#     """
#     Handles /play command
#     :param message: Telegram message with "/play" text
#     :param session: DB connection session
#     """
#     await session.merge(PlayerScore(user_id=message.from_user.id, score=0))
#     await session.commit()

#     await message.answer("Your score: 0", reply_markup=generate_balls())


# @router.message(Command("top"))
# async def cmd_top(message: Message, session: AsyncSession):
#     """
#     Handles /top command. Show top 5 players
#     :param message: Telegram message with "/top" text
#     :param session: DB connection session
#     """
#     sql = select(PlayerScore).order_by(PlayerScore.score.desc()).limit(5)
#     text_template = "Top 5 players:\n\n{scores}"
#     top_players_request = await session.execute(sql)
#     players = top_players_request.scalars()

#     score_entries = [f"{index+1}. ID{item.user_id}: {html.bold(item.score)}" for index, item in enumerate(players)]
#     score_entries_text = "\n".join(score_entries)\
#         .replace(f"{message.from_user.id}", f"{message.from_user.id} (it's you!)")
#     await message.answer(text_template.format(scores=score_entries_text), parse_mode="HTML")
