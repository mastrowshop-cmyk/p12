import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMIN_GROUP_ID, CHANNEL_ID

bot = Bot(TOKEN)
dp = Dispatcher()

# =========================
#     ИНЛАЙН КЛАВИАТУРА
# =========================
admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Ответить", callback_data="reply"),
            InlineKeyboardButton(text="Отклонить", callback_data="reject"),
            InlineKeyboardButton(text="Принять", callback_data="approve"),
        ],
        [
            InlineKeyboardButton(text="🚫 Забанить", callback_data="ban_user")
        ]
    ]
)

# =========================
#         /start
# =========================
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Подслушано АК")

# =========================
#  ПЕРЕСЫЛКА СООБЩЕНИЙ
# =========================
@dp.message()
async def forward_to_admins(message: types.Message):

    user = message.from_user
    username = f"@{user.username}" if user.username else user.full_name
    text = message.text or message.caption or ""

    sent_msg = None

    # отправка медиа
    if message.photo:
        sent_msg = await bot.send_photo(
            ADMIN_GROUP_ID,
            message.photo[-1].file_id,
            caption=text,
            reply_markup=admin_keyboard
        )
    elif message.video:
        sent_msg = await bot.send_video(
            ADMIN_GROUP_ID,
            message.video.file_id,
            caption=text,
            reply_markup=admin_keyboard
        )
    elif message.document:
        sent_msg = await bot.send_document(
            ADMIN_GROUP_ID,
            message.document.file_id,
            caption=text,
            reply_markup=admin_keyboard
        )
    elif message.voice:
        sent_msg = await bot.send_voice(
            ADMIN_GROUP_ID,
            message.voice.file_id,
            reply_markup=admin_keyboard
        )
        if text:
            await bot.send_message(ADMIN_GROUP_ID, text)
    else:
        sent_msg = await bot.send_message(
            ADMIN_GROUP_ID,
            text,
            reply_markup=admin_keyboard
        )

    # информация об авторе
    info = (
        f"👤 От: {username}\n"
        f"🆔 ID: `{user.id}`"
    )

    await bot.send_message(
        ADMIN_GROUP_ID,
        info,
        parse_mode="Markdown",
        reply_to_message_id=sent_msg.message_id
    )

    await message.answer("Отправлено 👌")

# =========================
#     ОБРАБОТЧИК КНОПОК
# =========================
@dp.callback_query(lambda c: c.data in ["reply", "reject", "approve"])
async def process_buttons(callback: types.CallbackQuery):
    action = callback.data
    msg = callback.message

    # убираем кнопки
    try:
        await msg.edit_reply_markup(reply_markup=None)
    except:
        pass

    # ===== ПРИНЯТЬ =====
    if action == "approve":

        # отправка в канал
        if msg.photo:
            await bot.send_photo(CHANNEL_ID, msg.photo[-1].file_id, caption=msg.caption)
        elif msg.video:
            await bot.send_video(CHANNEL_ID, msg.video.file_id, caption=msg.caption)
        elif msg.document:
            await bot.send_document(CHANNEL_ID, msg.document.file_id, caption=msg.caption)
        elif msg.voice:
            await bot.send_voice(CHANNEL_ID, msg.voice.file_id)
        else:
            await bot.send_message(CHANNEL_ID, msg.text)

        notif = await msg.answer("✅ Опубликовано в канале.")
        await asyncio.sleep(3)
        await notif.delete()
        await callback.answer()

    # ===== ОТКЛОНИТЬ =====
    elif action == "reject":
        notif = await msg.answer("❌ Сообщение отклонено.")
        await asyncio.sleep(3)
        await notif.delete()
        await callback.answer()

    # ===== ОТВЕТИТЬ =====
    elif action == "reply":
        await msg.answer("Напишите ответ пользователю реплаем на сообщение с его ID.")
        await callback.answer("Режим ответа включён")

# =========================
#        БАН КНОПКОЙ
# =========================
@dp.callback_query(lambda c: c.data == "ban_user")
async def ban_button(callback: types.CallbackQuery):
    msg = callback.message

    # убираем кнопки
    try:
        await msg.edit_reply_markup(reply_markup=None)
    except:
        pass

    # ищем айди
    target = msg.reply_to_message or msg
    content = target.text or target.caption or ""

    user_id = None
    for line in content.split("\n"):
        if "ID:" in line:
            try:
                user_id = int(line.replace("🆔 ID:", "").replace("ID:", "").replace("`", "").strip())
            except:
                pass

    if not user_id:
        await msg.answer("❌ Не удалось найти ID.")
        return

    try:
        await bot.ban_chat_member(ADMIN_GROUP_ID, user_id)
        notif = await msg.answer(f"🚫 Пользователь {user_id} забанен.")
        await asyncio.sleep(3)
        await notif.delete()
        await callback.answer()
    except Exception as e:
        await msg.answer(f"Ошибка: {e}")

# =========================
#   ОТВЕТ АДМИНА ПОЛЬЗОВАТЕЛЮ
# =========================
@dp.message(lambda msg: msg.chat.id == ADMIN_GROUP_ID and msg.reply_to_message)
async def admin_reply(message: types.Message):
    replied = message.reply_to_message
    target = replied.reply_to_message or replied

    content = target.text or target.caption or ""

    user_id = None
    for line in content.split("\n"):
        if "ID:" in line:
            try:
                user_id = int(line.replace("🆔 ID:", "").replace("ID:", "").replace("`", "").strip())
            except:
                pass

    if not user_id:
        return await message.answer("❌ Не удалось определить ID пользователя.")

    await bot.send_message(user_id, "Ответ администрации:\n\n" + message.text)
    await message.answer("Ответ отправлен 👍")

# =========================
#           /unban
# =========================
@dp.message(lambda msg: msg.chat.id == ADMIN_GROUP_ID and msg.text.startswith("/unban"))
async def unban_user(message: types.Message):

    replied = message.reply_to_message

    if not replied:
        return await message.answer("❌ Используй /unban ответом на сообщение с ID.")

    target = replied.reply_to_message or replied
    content = target.text or target.caption or ""

    user_id = None
    for line in content.split("\n"):
        if "ID:" in line:
            try:
                user_id = int(line.replace("🆔 ID:", "").replace("ID:", "").replace("`", "").strip())
            except:
                pass

    if not user_id:
        return await message.answer("❌ Не удалось найти ID.")

    try:
        await bot.unban_chat_member(ADMIN_GROUP_ID, user_id)
        notif = await message.answer(f"♻ Пользователь {user_id} разбанен.")
        await asyncio.sleep(3)
        await notif.delete()
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# =========================
#         START BOT
# =========================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
