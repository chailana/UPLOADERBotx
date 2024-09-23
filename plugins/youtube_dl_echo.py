@Clinton.on_message(filters.private & ~filters.via_bot & filters.regex(pattern=".*http.*"))
async def echo(bot, update):
    await AddUser(bot, update)
    
    # Correcting the reference to the message ID
    imog = await update.reply_text("Processing...⚡", reply_to_message_id=update.id)
    
    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None
    url = update.text

    if "|" in url:
        url_parts = url.split("|")
        if len(url_parts) == 2:
            url = url_parts[0]
            file_name = url_parts[1]
        elif len(url_parts) == 4:
            url = url_parts[0]
            file_name = url_parts[1]
            youtube_dl_username = url_parts[2]
            youtube_dl_password = url_parts[3]
        else:
            for entity in update.entities:
                if entity.type == "text_link":
                    url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    url = url[o:o + l]
        if url is not None:
            url = url.strip()
        if file_name is not None:
            file_name = file_name.strip()
        if youtube_dl_username is not None:
            youtube_dl_username = youtube_dl_username.strip()
        if youtube_dl_password is not None:
            youtube_dl_password = youtube_dl_password.strip()
        logger.info(url)
        logger.info(file_name)
    else:
        for entity in update.entities:
            if entity.type == "text_link":
                url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                url = url[o:o + l]

    if Config.HTTP_PROXY != "":
        command_to_exec = [
            "yt-dlp",
            "--no-warnings",
            "--youtube-skip-dash-manifest",
            "-j",
            url,
            "--proxy", Config.HTTP_PROXY
        ]
    else:
        command_to_exec = [
            "yt-dlp",
            "--no-warnings",
            "--youtube-skip-dash-manifest",
            "-j",
            url
        ]

    if youtube_dl_username is not None:
        command_to_exec.append("--username")
        command_to_exec.append(youtube_dl_username)

    if youtube_dl_password is not None:
        command_to_exec.append("--password")
        command_to_exec.append(youtube_dl_password)

    process = await asyncio.create_subprocess_exec(*command_to_exec,
                                                   stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    if e_response and "nonnumeric port" not in e_response:
        error_message = e_response.replace(Translation.ERROR_YTDLP, "")
        if "This video is only available for registered users." in error_message:
            error_message = Translation.SET_CUSTOM_USERNAME_PASSWORD
        else:
            error_message = "Invalid URL 🚸"
        
        await bot.send_message(chat_id=update.chat.id,
                               text=Translation.NO_VOID_FORMAT_FOUND.format(str(error_message)),
                               disable_web_page_preview=True, parse_mode="html",
                               reply_to_message_id=update.id)
        await imog.delete()
        return False

    if t_response:
        response_json = json.loads(t_response.split("\n")[0])
        save_ytdl_json_path = Config.DOWNLOAD_LOCATION + f"/{update.from_user.id}.json"
        with open(save_ytdl_json_path, "w", encoding="utf8") as outfile:
            json.dump(response_json, outfile, ensure_ascii=False)

        inline_keyboard = []
        duration = response_json.get("duration")

        if "formats" in response_json:
            for formats in response_json["formats"]:
                format_id = formats.get("format_id")
                format_string = formats.get("format_note") or formats.get("format")
                format_ext = formats.get("ext")
                approx_file_size = humanbytes(formats.get("filesize", ""))

                cb_string_video = f"video|{format_id}|{format_ext}"
                cb_string_file = f"file|{format_id}|{format_ext}"

                if format_string and "audio only" not in format_string:
                    ikeyboard = [
                        InlineKeyboardButton(f"🎬 {format_string} video {approx_file_size}", callback_data=cb_string_video.encode("UTF-8")),
                        InlineKeyboardButton(f"📂 {format_ext} {approx_file_size}", callback_data=cb_string_file.encode("UTF-8"))
                    ]
                else:
                    ikeyboard = [
                        InlineKeyboardButton(f"SVideo [{approx_file_size}]", callback_data=cb_string_video.encode("UTF-8")),
                        InlineKeyboardButton(f"DFile [{approx_file_size}]", callback_data=cb_string_file.encode("UTF-8"))
                    ]
                inline_keyboard.append(ikeyboard)

            if duration:
                cb_string_64 = "audio|64k|mp3"
                cb_string_128 = "audio|128k|mp3"
                cb_string_320 = "audio|320k|mp3"

                inline_keyboard.append([
                    InlineKeyboardButton("🎵 MP3 (64 kbps)", callback_data=cb_string_64.encode("UTF-8")),
                    InlineKeyboardButton("🎵 MP3 (128 kbps)", callback_data=cb_string_128.encode("UTF-8")),
                    InlineKeyboardButton("🎵 MP3 (320 kbps)", callback_data=cb_string_320.encode("UTF-8"))
                ])

        reply_markup = InlineKeyboardMarkup(inline_keyboard)
        await imog.delete()
        await bot.send_message(chat_id=update.chat.id,
                               text=Translation.FORMAT_SELECTION + "\n" + Translation.SET_CUSTOM_USERNAME_PASSWORD,
                               reply_markup=reply_markup,
                               parse_mode="html",
                               reply_to_message_id=update.id)
