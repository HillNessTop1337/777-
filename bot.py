import telebot
from telebot import types
import threading
import time

# Токен вашего бота
TOKEN = "7072738806:AAF6oQ3-LQO7D__1x_4Dze8VS4QhGTyKqHQ"
bot = telebot.TeleBot(TOKEN)

# Список для хранения замученных пользователей
muted_users = []

# Функция проверки, является ли пользователь администратором
def is_admin(chat_id, user_id):
    member = bot.get_chat_member(chat_id, user_id)
    return member.status in ['administrator', 'creator']

# Функция конвертации времени из минут в секунды
def convert_time_to_seconds(time_str):
    units = time_str[-1]  # последний символ указывает единицу измерения
    number = int(time_str[:-1])  # число до последнего символа

    if units == "m":  # минуты
        return number * 60
    elif units == "h":  # часы
        return number * 3600
    elif units == "d":  # дни
        return number * 86400
    else:
        return number  # если указаны секунды

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я чат-менеджер. Используйте /help для списка команд.")

# Команда /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
    Доступные команды:
    /kick [@username] [причина] - Кикнуть пользователя
    /ban [@username] [время] [причина] - Забанить пользователя на определенное время
    /mute [@username] [время] [причина] - Замутить пользователя на определенное время
    /unmute [@username] [причина] - Размутить пользователя
    /joke - Рассказать случайную шутку
    /help - Показать это сообщение

    Время может быть указано в формате: 10m (минуты), 1h (часы), 1d (дни).
    """
    bot.reply_to(message, help_text)

# Функция для автоматического снятия мута
def unmute_after_time(chat_id, user_id, duration):
    time.sleep(duration)
    if user_id in muted_users:
        muted_users.remove(user_id)
        bot.send_message(chat_id, f"Пользователь {user_id} был автоматически размучен после истечения времени.")

# Команда кикнуть пользователя
@bot.message_handler(commands=['kick'])
def kick_user(message):
    if not message.reply_to_message:
        bot.reply_to(message, "Эту команду нужно использовать в ответ на сообщение.")
        return
    
    if is_admin(message.chat.id, message.from_user.id):
        user_to_kick = message.reply_to_message.from_user.id
        reason = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "Причина не указана."
        bot.kick_chat_member(message.chat.id, user_to_kick)
        bot.send_message(message.chat.id, f"Пользователь {message.reply_to_message.from_user.username} был кикнут. Причина: {reason}")
    else:
        bot.reply_to(message, "Эта команда доступна только администраторам.")

# Команда забанить пользователя
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if not message.reply_to_message:
        bot.reply_to(message, "Эту команду нужно использовать в ответ на сообщение.")
        return
    
    if is_admin(message.chat.id, message.from_user.id):
        args = message.text.split(maxsplit=2)
        if len(args) < 2:
            bot.reply_to(message, "Укажите время для бана. Пример: /ban @username 10m причина")
            return
        
        user_to_ban = message.reply_to_message.from_user.id
        time_str = args[1]
        reason = args[2] if len(args) > 2 else "Причина не указана."

        # Конвертация времени
        ban_duration = convert_time_to_seconds(time_str)

        # Бан пользователя на указанное время
        bot.ban_chat_member(message.chat.id, user_to_ban, until_date=int(time.time() + ban_duration))
        bot.send_message(message.chat.id, f"Пользователь {message.reply_to_message.from_user.username} был забанен на {time_str}. Причина: {reason}")
    else:
        bot.reply_to(message, "Эта команда доступна только администраторам.")

# Команда замутить пользователя
@bot.message_handler(commands=['mute'])
def mute_user(message):
    if not message.reply_to_message:
        bot.reply_to(message, "Эту команду нужно использовать в ответ на сообщение.")
        return
    
    if is_admin(message.chat.id, message.from_user.id):
        args = message.text.split(maxsplit=2)
        if len(args) < 2:
            bot.reply_to(message, "Укажите время для мута. Пример: /mute @username 10m причина")
            return

        user_to_mute = message.reply_to_message.from_user.id
        time_str = args[1]
        reason = args[2] if len(args) > 2 else "Причина не указана."

        # Конвертация времени
        mute_duration = convert_time_to_seconds(time_str)

        # Мут пользователя
        muted_users.append(user_to_mute)
        bot.send_message(message.chat.id, f"Пользователь {message.reply_to_message.from_user.username} был замучен на {time_str}. Причина: {reason}")

        # Запускаем поток для автоматического размучивания после истечения времени
        threading.Thread(target=unmute_after_time, args=(message.chat.id, user_to_mute, mute_duration)).start()
    else:
        bot.reply_to(message, "Эта команда доступна только администраторам.")

# Команда размутить пользователя
@bot.message_handler(commands=['unmute'])
def unmute_user(message):
    if not message.reply_to_message:
        bot.reply_to(message, "Эту команду нужно использовать в ответ на сообщение.")
        return
    
    if is_admin(message.chat.id, message.from_user.id):
        user_to_unmute = message.reply_to_message.from_user.id
        reason = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "Причина не указана."
        if user_to_unmute in muted_users:
            muted_users.remove(user_to_unmute)
            bot.send_message(message.chat.id, f"Пользователь {message.reply_to_message.from_user.username} был размучен. Причина: {reason}")
        else:
            bot.reply_to(message, "Этот пользователь не был замучен.")
    else:
        bot.reply_to(message, "Эта команда доступна только администраторам.")

# Фильтрация сообщений от замученных пользователей
@bot.message_handler(func=lambda message: message.from_user.id in muted_users)
def filter_muted_messages(message):
    bot.delete_message(message.chat.id, message.message_id)

# Развлекательная команда /joke
import random

jokes = [
    "Почему программисты любят осень? Потому что осень — это 'фолл', а фолл — это ошибка.",
    "Как программист делает предложение? printf('Ты выйдешь за меня?\\n');",
    "Чем отличается программист от обычного человека? Программист знает, что два плюс два не всегда четыре."
]

@bot.message_handler(commands=['joke'])
def tell_joke(message):
    bot.reply_to(message, random.choice(jokes))

# Запуск бота
bot.polling()
