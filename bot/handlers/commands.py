from aiogram import Router, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from bot.db.models import ChatMessage
from bot.static_text import greeting, new_dialog_start

router = Router(name="commands-router")


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handles /start command
    :param message: Telegram message with "/start" text
    """
    await message.answer(greeting)

@router.message(Command("reset"))
async def cmd_start_new(message: Message, session: AsyncSession):
    """
    Handles /start_new command
    :param message: Telegram message with "/start_new" text
    """

    user_id = message.from_user.id
    user_first_name = message.from_user.first_name
    user_last_name = message.from_user.last_name
    username = message.from_user.username

    # Create a new ChatMessage object with is_new_dialog_start set to True
    new_dialog_message = ChatMessage(
        user_id=user_id,
        user_first_name=user_first_name,
        user_last_name=user_last_name,
        username=username,
        role='user',
        content=new_dialog_start,  # the content of the system message
        is_text=True,
        date_time=datetime.now(),
        is_new_dialog_start=True  # Set the flag to indicate start of new dialog
    )

    # Add the new message to the session and commit
    session.add(new_dialog_message)
    await session.commit()

    await message.answer(new_dialog_start)





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
