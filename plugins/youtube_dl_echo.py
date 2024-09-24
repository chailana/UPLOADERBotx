 are correctly set up.
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | X-Noid | @DC4_WARRIOR

import logging
import requests
import urllib.parse
import filetype
import os
import time
import shutil
import tldextract
import asyncio
import json
import math
from PIL import Image
from database.adduser import AddUser
from translation import Translation
from pyrogram import filters, Client as Clinton
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ParseMode

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Import configuration based on environment variable
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

# Helper functions for progress display
from helper_funcs.display_progress import humanbytes

@Clinton.on_message(filters.private & filters.regex(pattern=".*http.*"))
async def echo(bot, update):
    await AddUser(bot, update)

    # Check if message has message_id attribute and handle accordingly
    if hasattr(update, 'message_id'):
        imog = await update.reply_text("Processing...⚡", reply_to_message_id=update.message_id)
    else:
        imog = await update.reply_text("Processing...⚡")

    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None
    url = update.text.strip()

    # Parse URL and optional parameters from the message text
    if "|" in url:
        url_parts = url.split("|")
        if len(url_parts) == 2:
            url, file_name = map(str.strip, url_parts)
        elif len(url_parts) == 4:
            url, file_name, youtube_dl_username, youtube_dl_password = map(str.strip, url_parts)

    logger.info(f"URL: {url}")
    logger.info(f"File Name: {file_name}")

    # Construct the command to execute yt-dlp with necessary parameters
    command_to_exec = [
        "yt-dlp",
        "--no-warnings",
        "--youtube-skip-dash-manifest",
        "-j",
        url,
    ]

    if Config.HTTP_PROXY:
        command_to_exec.append("--proxy")
        command_to_exec.append(Config.HTTP_PROXY)

    if youtube_dl_username:
        command_to_exec += ["--username", youtube_dl_username]

    if youtube_dl_password:
        command_to_exec += ["--password", youtube_dl_password]

    # Execute the yt-dlp command as a subprocess
    process = await asyncio.create_subprocess_exec(
        *command_to_exec,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Wait for the subprocess to finish and capture output
    stdout, stderr = await process.communicate()
    
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    # Handle errors from yt-dlp execution
    if e_response and "nonnumeric port" not in e_response:
        error_message = e_response.replace(
            "please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output.", 
            ""
        )
        
        if "This video is only available for registered users." in error_message:
            error_message += Translation.SET_CUSTOM_USERNAME_PASSWORD
        
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NO_VOID_FORMAT_FOUND.format(str(error_message)),
            reply_to_message_id=getattr(update, 'message_id', None),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    # Process successful response from yt-dlp
    if t_response:
        first_line = t_response.split("\n")[0]
        response_json = json.loads(first_line)
        
        save_ytdl_json_path = os.path.join(Config.DOWNLOAD_LOCATION, f"{update.from_user.id}.json")
        
        with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
            json.dump(response_json, outfile, ensure_ascii=False)

        inline_keyboard = []
        
        duration = response_json.get("duration")

        # Build inline keyboard based on available formats in response JSON
        if "formats" in response_json:
            for formats in response_json["formats"]:
                format_id = formats.get("format_id")
                format_string = formats.get("format_note") or formats.get("format")
                format_ext = formats.get("ext")
                approx_file_size = humanbytes(formats.get("filesize", 0))

                cb_string_video = f"video|{format_id}|{format_ext}"
                cb_string_file = f"file|{format_id}|{format_ext}"

                ikeyboard = [
                    InlineKeyboardButton(f"S {format_string} video {approx_file_size}", callback_data=cb_string_video.encode("UTF-8")),
                    InlineKeyboardButton(f"D {format_ext} {approx_file_size}", callback_data=cb_string_file.encode("UTF-8")),
                ]
                
                inline_keyboard.append(ikeyboard)

            # Add audio options if duration is available
            if duration is not None:
                inline_keyboard.append([
                    InlineKeyboardButton("MP3 (64 kbps)", callback_data="audio|64k|mp3".encode("UTF-8")),
                    InlineKeyboardButton("MP3 (128 kbps)", callback_data="audio|128k|mp3".encode("UTF-8")),
                    InlineKeyboardButton("MP3 (320 kbps)", callback_data="audio|320k|mp3".encode("UTF-8")),
                ])

        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        
        await imog.delete(True)
        
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.FORMAT_SELECTION + "\n" + Translation.SET_CUSTOM_USERNAME_PASSWORD,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=getattr(update, 'message_id', None),
        )
    
    else:
        # Fallback for nonnumeric port case (e.g., seedbox.io)
        inline_keyboard = [
            [
                InlineKeyboardButton("SVideo", callback_data="video|OFL|ENON".encode("UTF-8")),
                InlineKeyboardButton("DFile", callback_data="file|LFO|NONE".encode("UTF-8")),
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        
        await imog.delete(True)
        
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.FORMAT_SELECTION,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=getattr(update, 'message_id', None),
        )

@Clinton.on_callback_query()
async def youtube_dl_call_back(bot, update: CallbackQuery):
    # Ensure that we have a valid callback query and data is present.
    
    if not update.data:
        await bot.answer_callback_query(
            callback_query_id=update.id,
            text="Invalid request.",
            show_alert=True
        )
        return

    # Check if the callback is from a message reply.
    
    if update.message and update.message.reply_to_message:
        youtube_dl_url = update.message.reply_to_message.text
        
    else:
        await bot.answer_callback_query(
            callback_query_id=update.id,
            text="Please reply to a message containing a valid URL.",
            show_alert=True
        )
        
        return

    # Extract format information from callback data.
    
    callback_data_parts = update.data.split('|')
    
    if len(callback_data_parts) < 3:
        
        await bot.answer_callback_query(
            callback_query_id=update.id,
            text="Invalid format selection.",
            show_alert=True
        )
        
        return

    action_type, format_id, format_ext = callback_data_parts

    logger.info(f"Selected format: {action_type}, ID: {format_id}, Extension: {format_ext}")

    # Here you can continue with your yt-dlp command execution or any other processing needed.
    
    # Example of sending a confirmation message back to the user.
    
    await bot.send_message(
        chat_id=update.message.chat.id,
        text=f"You selected {action_type} with format ID {format_id} and extension {format_ext}.",
        reply_to_message_id=update.message.message_id,
    )

# Note: Ensure that all necessary imports and configurations are correctly set up.
