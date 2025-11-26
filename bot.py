import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMIN_GROUP_ID, CHANNEL_ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)


# === АВТОУДАЛЕНИЕ СЛУЖЕБНЫХ СООБЩЕНИЙ ===
async def auto_delete(msg, delay=5):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass


# === КЛАВИАТУРА ДЛЯ АДМИНОВ ===
admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Ответить", callback_data="reply"),
            InlineKeyboardButton(text="Отклонить", callback_data="reject"),
            InlineKeyboardButton(text="Принять", callback_data="approve"),
            InlineKeyboardButton(text="Забанить", callback_data="ban"),
        ]
    ]
)


# === ПРОВЕРКА НА БАН ===
def is_banned(user_id: int) -> bool:
    try:
        with open("banlist.txt", "r") as f:
            banned = f.read().splitlines()
        return str(user_id) in banned
    except FileNotFoundError:
        return False


# === КОМАНДА START ===
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Подслушано АК")


# === ПОЛЬЗОВАТЕЛЬ ПИШЕТ БОТУ ===
@dp.message_handler(content_types=types.ContentTypes.ANY)
async def forward_to_admins(message: types.Message):
    user = message.from_user

    # проверка бана
    if is_banned(user.id):
        m = await message.answer("⛔ Вы забанены и не можете отправлять сообщения.")
        asyncio.create_task(auto_delete(m))
        return

    username = f"@{user.username}" if user.username else user.full_name
    text = message.text or message.caption or ""

    sent_msg = None

    # отправка сообщения админу
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

    # инфа о пользователе
    info = f"👤 От: {username}\n🆔 ID: <code>{user.id}</code>"

    await bot.send_message(
        ADMIN_GROUP_ID,
        info,
        reply_to_message_id=sent_msg.message_id
    )

    m = await message.answer("Отправлено 👌")
    asyncio.create_task(auto_delete(m))


# === ОБРАБОТКА КНОПОК ===
@dp.callback_query_handler(lambda c: c.data in ["reply", "reject", "approve", "ban"])
async def process_buttons(callback: types.CallbackQuery):
    action = callback.data
    msg = callback.message

    # удалить inline-меню
    try:
        await msg.edit_reply_markup(None)
    except:
        pass

    # =======================
    # ПРИНЯТЬ → публикация
    # =======================
    if action == "approve":
        try:
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

            m = await msg.answer("✅ Опубликовано в канале")
            asyncio.create_task(auto_delete(m))

        except Exception as e:
            m = await msg.answer(f"Ошибка публикации: {e}")
            asyncio.create_task(auto_delete(m))

        await callback.answer()
        return

    # =======================
    # ОТКЛОНИТЬ
    # =======================
    if action == "reject":
        m = await msg.answer("❌ Сообщение отклонено.")
        asyncio.create_task(auto_delete(m))
        await callback.answer()
        return

    # =======================
    # ОТВЕТИТЬ
    # =======================
    if action == "reply":
        m = await msg.answer("Напишите ответ реплаем на сообщение с ID пользователя.")
        asyncio.create_task(auto_delete(m))
        await callback.answer()
        return

    # =======================
    # БАН
    # =======================
    if action == "ban":
        content = msg.reply_to_message.text if msg.reply_to_message else ""
        user_id = None

        for line in content.split("\n"):
            if "ID" in line:
                try:
                    user_id = int(
                        line.replace("ID:", "")
                        .replace("🆔", "")
                        .replace("<code>", "")
                        .replace("</code>", "")
                        .strip()
                    )
                except:
                    pass

        if not user_id:
            m = await msg.answer("❌ Не могу найти ID пользователя.")
            asyncio.create_task(auto_delete(m))
            await callback.answer()
            return

        # запись в банлист
        with open("banlist.txt", "a") as f:
            f.write(str(user_id) + "\n")

        m = await msg.answer(f"⛔ Пользователь <code>{user_id}</code> забанен.")
        asyncio.create_task(auto_delete(m))
        await callback.answer()
        return


# === АДМИН ОТВЕЧАЕТ ПОЛЬЗОВАТЕЛЮ ===
@dp.message_handler(lambda m: m.chat.id == ADMIN_GROUP_ID, content_types=types.ContentTypes.TEXT)
async def admin_reply(message: types.Message):
    if not message.reply_to_message:
        return

    content = message.reply_to_message.text or ""
    user_id = None

    for line in content.split("\n"):
        if "ID" in line:
            try:
                user_id = int(
                    line.replace("ID:", "")
                    .replace("🆔", "")
                    .replace("<code>", "")
                    .replace("</code>", "")
                    .strip()
                )
            except:
                pass

    if not user_id:
        m = await message.answer("❌ Не найден ID пользователя.")
        asyncio.create_task(auto_delete(m))
        return

    await bot.send_message(user_id, f"Ответ администрации:\n\n{message.text}")

    m = await message.answer("Ответ отправлен 👍")
    asyncio.create_task(auto_delete(m))


# === СТАРТ БОТА ===
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
