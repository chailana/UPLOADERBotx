# (c) @AbirHasan2005 | @PredatorHackerzZ

import asyncio
from config import Config
from pyrogram import Client
from pyrogram.errors import FloodWait, UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode  # Importing ParseMode

async def ForceSub(bot: Client, cmd: Message):
    try:
        user = await bot.get_chat_member(
            chat_id=(int(Config.UPDATES_CHANNEL) if Config.UPDATES_CHANNEL.startswith("-100") else Config.UPDATES_CHANNEL),
            user_id=cmd.from_user.id
        )
        
        if user.status == "banned":
            await bot.send_message(
                chat_id=cmd.from_user.id,
                text="Access Denied ⚠. Contact my [Support Group](https://t.me/TeleRoid14).",
                parse_mode=ParseMode.MARKDOWN,  # Use ParseMode enum
                disable_web_page_preview=True
            )
            return 400
            
    except UserNotParticipant:
        await bot.send_message(
            chat_id=cmd.from_user.id,
            text="**Please Join My Updates Channel to use this Bot!**\n\nDue to Overload, Only Channel Subscribers can use the Bot!\n\nAnd Still If Bot Asks For Joining Updates Channel then Join @MoviesFlixers_DL this Channel too.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🤖 Join Updates Channel", url="https://t.me/TeleRoidGroup")
                    ]
                ]
            ),
            parse_mode=ParseMode.MARKDOWN  # Use ParseMode enum
        )
        return 400
        
    except Exception as e:
        print(f"An error occurred: {e}")  # Log the exception for debugging
        await bot.send_message(
            chat_id=cmd.from_user.id,
            text="Something Went Wrong. Contact my [Support Group](https://t.me/TeleRoid14)",
            parse_mode=ParseMode.MARKDOWN,  # Use ParseMode enum
            disable_web_page_preview=True
        )
        return 400
        
    return 200
