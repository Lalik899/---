import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

BOT_TOKEN = 'токен'
ADMIN_USER_ID = айди админа


# ================== ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ==================
def init_db():
    connection = sqlite3.connect('id.db')
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Пользователи (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_user INTEGER UNIQUE,
        first_name TEXT NOT NULL,
        user_name TEXT NOT NULL,
        last_name TEXT
    )
    ''')
    connection.commit()
    connection.close()


# ================== КОМАНДА /start ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    keyboard = [
        [InlineKeyboardButton("Регистрация", callback_data='register')],
        [InlineKeyboardButton("Изменить мои данные", callback_data='edit')]
    ]

    if user_id == ADMIN_USER_ID:
        keyboard.append(
            [InlineKeyboardButton("Показать всех пользователей", callback_data='show_all')]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=reply_markup
    )


# ================== ОБРАБОТКА КНОПОК ==================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id

    connection = sqlite3.connect('id.db')
    cursor = connection.cursor()

    # ---------- РЕГИСТРАЦИЯ ----------
    elif query.data == 'register':
        cursor.execute('SELECT 1 FROM Пользователи WHERE id_user = ?', (user_id,))
        exists = cursor.fetchone()

        if exists:
            text = "❗ Вы уже зарегистрированы"
        else:
            cursor.execute(
                'INSERT INTO Пользователи (id_user, first_name, user_name, last_name) VALUES (?, ?, ?, ?)',
                (
                    user_id,
                    user.first_name,
                    user.username or "Нетusername",
                    user.last_name or ""
                )
            )
            connection.commit()
            text = f"✅ Регистрация успешна, {user.first_name}!"

        await query.edit_message_text(text=text)

    # ---------- ПРОСМОТР ВСЕХ ----------
    elif query.data == 'show_all':
        if user_id != ADMIN_USER_ID:
            await query.edit_message_text("⛔ У вас нет прав доступа")
        else:
            cursor.execute('SELECT * FROM Пользователи')
            users = cursor.fetchall()

            if not users:
                text = "База данных пуста"
            else:
                text = "👥 Все пользователи:\n\n"
                for u in users:
                    text += (
                        f"ID: {u[1]}\n"
                        f"Имя: {u[2]}\n"
                        f"Username: @{u[3]}\n"
                        f"Фамилия: {u[4]}\n"
                        f"{'-'*20}\n"
                    )

            await query.edit_message_text(text=text)

    # ---------- ИЗМЕНЕНИЕ ДАННЫХ ----------
    elif query.data == 'edit':
        cursor.execute('SELECT 1 FROM Пользователи WHERE id_user = ?', (user_id,))
        exists = cursor.fetchone()

        if not exists:
            await query.edit_message_text("❗ Сначала зарегистрируйтесь")
        else:
            context.user_data['edit'] = True
            await query.edit_message_text(
                "✏️ Отправьте новые данные:\n\n"
                "Имя, username, фамилия"
            )

    connection.close()


# ================== ПОЛУЧЕНИЕ НОВЫХ ДАННЫХ ==================
async def edit_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('edit'):
        return

    try:
        first_name, username, last_name = map(str.strip, update.message.text.split(','))

        connection = sqlite3.connect('id.db')
        cursor = connection.cursor()
        cursor.execute(
            '''
            UPDATE Пользователи
            SET first_name = ?, user_name = ?, last_name = ?
            WHERE id_user = ?
            ''',
            (first_name, username, last_name, update.message.from_user.id)
        )
        connection.commit()
        connection.close()

        context.user_data['edit'] = False
        await update.message.reply_text("✅ Данные обновлены")

    except ValueError:
        await update.message.reply_text("❌ Неверный формат")


# ================== ЗАПУСК БОТА ==================
def main():
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, edit_user_data))

    application.run_polling()


if __name__ == '__main__':
    main()
