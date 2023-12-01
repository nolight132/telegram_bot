import logging
import requests
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    BotCommand
)
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler
)


API_URL = "https://api.quotable.io"
DEFAULT_STATE, TYPING_TAG_STATE = range(2)
__state__ = DEFAULT_STATE


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# COMMANDS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Random quote", callback_data="random")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("I am a bot, whose sole purpose is to send you quotes.\n\nAt the moment, only these commands are supported:", reply_markup=reply_markup)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu to list all the available commands"""
    keyboard = [
        [InlineKeyboardButton("Random quote", callback_data="random")],
        [InlineKeyboardButton("Random quote by tag", callback_data="random_by_tag")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("This is a list of all available commands:\n\n", reply_markup=reply_markup)

# LOGIC
def get_tags(message: str) -> list:
    tags = ["Tag 1", "Tag 2", "Tag 3"]
    return tags


def get_random_quote(author: bool) -> str:
    response = requests.get(API_URL + "/quotes/random")
    quote = '"' + response.json()[0]["content"] + '"'

    if author:
        author = response.json()[0]["author"]
        return f"{quote}\n\n- {author}"
    else:
        return quote


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I don't recognize this command.")


def main() -> None:
    """Start the bot."""
    application = ApplicationBuilder().token('6973604569:AAH2NChCYageGr2sbm0mTfeKResrn5ePVxY').build()

    start_handler = CommandHandler('start', start)
    random_handler = CommandHandler('random', random)
    random_by_tag_handler = CommandHandler('random_by_tag', random_by_tag)
    text_handler = MessageHandler(filters.TEXT, text_filter)
    unknown_handler = MessageHandler(filters.ALL, unknown)

    application.add_handler(start_handler)
    application.add_handler(CallbackQueryHandler(button_filter))
    application.add_handler(random_handler)
    application.add_handler(random_by_tag_handler)
    application.add_handler(text_handler)
    application.add_handler(unknown_handler)
    
    application.run_polling()


if __name__ == '__main__':
    main()