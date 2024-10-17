
import asyncio
from FileStream.bot import FileStream, multi_clients
from FileStream.utils.bot_utils import is_user_banned, is_user_exist, is_user_joined, gen_link, is_channel_banned, is_channel_exist, is_user_authorized
from FileStream.utils.database import Database
from FileStream.utils.file_properties import get_file_ids, get_file_info
from FileStream.config import Telegram
from pyrogram import filters, Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums.parse_mode import ParseMode
db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)

@FileStream.on_message(
    filters.private
    & (
            filters.document
            | filters.video
            | filters.video_note
            | filters.audio
            | filters.voice
            | filters.animation
            | filters.photo
    ),
    group=4,
)
async def private_receive_handler(bot: Client, message: Message):
    if not await is_user_authorized(message):
        return
    if await is_user_banned(message):
        return

    await is_user_exist(bot, message)
    if Telegram.FORCE_SUB:
        if not await is_user_joined(bot, message):
            return
    try:
        inserted_id = await db.add_file(get_file_info(message))
        await get_file_ids(False, inserted_id, multi_clients, message)
        reply_markup, stream_text = await gen_link(_id=inserted_id)
        await message.reply_text(
            text=stream_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            quote=True
        )
    except FloodWait as e:
        print(f"Sleeping for {str(e.value)}s")
        await asyncio.sleep(e.value)
        await bot.send_message(chat_id=Telegram.ULOG_CHANNEL,
                               text=f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ {str(e.value)}s ғʀᴏᴍ [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n\n**ᴜsᴇʀ ɪᴅ :** `{str(message.from_user.id)}`",
                               disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)


@FileStream.on_message(
    filters.channel
    & ~filters.forwarded
    & ~filters.media_group
    & (
            filters.document
            | filters.video
            | filters.video_note
            | filters.audio
            | filters.voice
            | filters.photo
    )
)
async def channel_receive_handler(bot: Client, message: Message):
    if await is_channel_banned(bot, message):
        return
    await is_channel_exist(bot, message)

    try:
        inserted_id = await db.add_file(get_file_info(message))
        await get_file_ids(False, inserted_id, multi_clients, message)
        reply_markup, stream_link = await gen_link(_id=inserted_id)
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.id,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Dᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ 📥",
                                       url=f"https://t.me/{FileStream.username}?start=stream_{str(inserted_id)}")]])
        )

    except FloodWait as w:
        print(f"Sleeping for {str(w.x)}s")
        await asyncio.sleep(w.x)
        await bot.send_message(chat_id=Telegram.ULOG_CHANNEL,
                               text=f"ɢᴏᴛ ғʟᴏᴏᴅᴡᴀɪᴛ ᴏғ {str(w.x)}s ғʀᴏᴍ {message.chat.title}\n\n**ᴄʜᴀɴɴᴇʟ ɪᴅ :** `{str(message.chat.id)}`",
                               disable_web_page_preview=True)
    except Exception as e:
        await bot.send_message(chat_id=Telegram.ULOG_CHANNEL, text=f"**#EʀʀᴏʀTʀᴀᴄᴋᴇʙᴀᴄᴋ:** `{e}`",
                               disable_web_page_preview=True)
        print(f"Cᴀɴ'ᴛ Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ!\nEʀʀᴏʀ:  **Gɪᴠᴇ ᴍᴇ ᴇᴅɪᴛ ᴘᴇʀᴍɪssɪᴏɴ ɪɴ ᴜᴘᴅᴀᴛᴇs ᴀɴᴅ ʙɪɴ Cʜᴀɴɴᴇʟ!{e}**")
        
@FileStream.on_message(filters.command(["link"]))
async def group_media_receive_handler(c: Client, m: Message):
    if m.from_user.id == Var.BOT_ID:
        return
    if not await fsub_handler(c, m):
        return
    try:
        msg = m.reply_to_message
        if msg is None or msg.text:
            return await m.reply_text("Reply To a Valid Media")
    except Exception as e:
        return await m.reply_text(f"Error: {e}")
 
    try:
        log_msg = await msg.forward(chat_id=Var.BIN_CHANNEL)

        f_name = get_name(log_msg)
        f_size = humanbytes(get_media_file_size(log_msg))
        f_owner = msg.from_user.first_name
        f_time = get_current_time()
        df_link = gen_direct_file_link(log_msg)
        meta = quote_plus(
            encode_string(f"{f_name}|{f_size}|{f_owner}|{f_time}|{df_link}")
        )
        url_id = quote_plus(str_to_enc(f"{log_msg.chat.id}/{log_msg.id}"))
        file_hash = get_hash(log_msg, Var.HASH_LENGTH)
        stream_link = f"{Var.URL}{log_msg.id}/{quote_plus(f_name)}?hash={file_hash}"
        short_stream_link = await gen_stream_link(url_id, stream_link, meta, short=True)
        logger.info(f"Generated link: {stream_link} for {msg.from_user.first_name}")

        msg_text = """<b><i>Your Link Generated !</i></b>\n\n<b>📂 File Name :</b> <i>{}</i>\n\n<b>📦 File Size :</b> <i>{}</i>\n\n<b>🚸 Note : Links are available as long as the bot is active.</b>"""

        await log_msg.reply_text(
            text=f"#NewFile \n\n**User Name :** [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n**User Id :** `{m.from_user.id}`\n**Stream Link :** {stream_link}",
            disable_web_page_preview=True,
            quote=True,
        )
        await m.reply_text(
            text=msg_text.format(f_name, f_size),
            quote=True,
            disable_web_page_preview=True,
            reply_markup=await generate_stream_button(
                m, short_stream_link, stream_link, df_link
            ),
        )
    except errors.ButtonUrlInvalid:
        log_msg = await msg.forward(chat_id=Var.BIN_CHANNEL)
        file_hash = get_hash(log_msg, Var.HASH_LENGTH)
        stream_link = (
            f"{Var.URL}{log_msg.id}/{quote_plus(get_name(msg))}?hash={file_hash}"
        )
        short_link = f"{Var.URL}{file_hash}{log_msg.id}"
        logger.info(f"Generated link: {stream_link} for {m.from_user.first_name}")

        await m.reply_text(
            text="<code>{}</code>\n\nShortened: {})".format(stream_link, short_link),
            quote=True,
            parse_mode=ParseMode.HTML,
        )
    except FloodWait as e:
        print(f"Sleeping for {str(e.x)}s")
        await asyncio.sleep(e.x)
        await c.send_message(
            chat_id=Var.BIN_CHANNEL,
            text=f"Got Floodwait Of {str(e.x)}s from [{m.from_user.first_name}](tg://user?id={m.from_user.id})\n\n**User Id :** `{str(m.from_user.id)}`",
            disable_web_page_preview=True,
        )

