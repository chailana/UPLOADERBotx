#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import os
import sqlite3

# the secret configuration specific things
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

# the Strings used for this "thing"
from translation import Translation
from helper_funcs.forcesub import ForceSub
from pyrogram import filters
from database.adduser import AddUser
from pyrogram import Client as Clinton
from pyrogram.enums import ParseMode  # Import ParseMode here
logging.getLogger("pyrogram").setLevel(logging.WARNING)

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, ForceReply


@Clinton.on_message(filters.private & filters.command(["help"]))
async def help_user(bot, message):
    await AddUser(bot, message)
    forcesub = await ForceSub(bot, message)
    if forcesub == 400:
        return
    await bot.send_message(
        chat_id=message.chat.id,
        text=Translation.HELP_TEXT,
        parse_mode=ParseMode.HTML,  # Changed here
        disable_web_page_preview=True,
        reply_to_message_id=message.id,  # Updated here
        reply_markup=Translation.HELP_BUTTONS
    )


@Clinton.on_message(filters.private & filters.command(["start"]))
async def start(bot, message):
    await AddUser(bot, message)
    forcesub = await ForceSub(bot, message)
    if forcesub == 400:
        return
    await bot.send_message(
        chat_id=message.chat.id,
        text=Translation.START_TEXT.format(message.from_user.mention),
        parse_mode=ParseMode.HTML,  # Changed here
        disable_web_page_preview=True,
        reply_to_message_id=message.id,  # Updated here
        reply_markup=Translation.START_BUTTONS
    )

@Clinton.on_message(filters.private & filters.command("about"))
async def about_user(bot, message):
    await AddUser(bot, message)
    forcesub = await ForceSub(bot, message)
    if forcesub == 400:
        return
    await bot.send_message(
        chat_id=message.chat.id,
        text=Translation.ABOUT_TEXT,
        parse_mode=ParseMode.HTML,  # Changed here
        disable_web_page_preview=True,
        reply_to_message_id=message.id,  # Updated here
        reply_markup=Translation.ABOUT_BUTTONS
    )
