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
    CallbackQueryHandler,
    ConversationHandler
)


API_URL = "https://api.quotable.io"
TYPING_TAG, TYPING_AUTHOR  = range(2)
COMMANDS = [
    'help'
    'random',
    'random_by_author',
    'menu',
    'start',
]

COMMANDS_KEYBOARD_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton('Random quote', callback_data='random')],
    [InlineKeyboardButton('Random quote by author', callback_data='random_by_author')],
    [
        InlineKeyboardButton('Menu', callback_data='menu'),
        InlineKeyboardButton('Help', callback_data='help')
    ],
    [InlineKeyboardButton('Start', callback_data='start')],
])


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# COMMANDS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """Executes on /start."""
    print(f'User {update.effective_chat.effective_name} just used a /start command.')
    if query:
        await query.edit_message_text('I am a bot, whose sole purpose is to send you quotes.\n\nAt the moment, only these commands are supported:', reply_markup=COMMANDS_KEYBOARD_MARKUP)
    else:
       await update.message.reply_text('I am a bot, whose sole purpose is to send you quotes.\n\nAt the moment, only these commands are supported:', reply_markup=COMMANDS_KEYBOARD_MARKUP)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """Menu to list all the available commands"""
    if query:
        await query.edit_message_text("This is a list of all available commands:\n\n<i>Tip: you don't have to use this menu, just type \"/\".</i>", parse_mode='HTML', reply_markup=COMMANDS_KEYBOARD_MARKUP)
    else:
        await update.message.reply_text("This is a list of all available commands:\n\n<i>Tip: you don't have to use this menu, just type \"/\".</i>", parse_mode='HTML', reply_markup=COMMANDS_KEYBOARD_MARKUP)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """Displays a help message."""
    global state
    if query:
        await query.edit_message_text(f"Hi, {update.effective_chat.first_name}, I am a bot!\n\nI can help you pick a quote. Type /menu for a list of available commands.")
        return
    await update.message.reply_text(f"Hi, {update.effective_chat.first_name}, I am a bot!\n\nI can help you pick a quote. Type /menu for a list of available commands.")


async def menu_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'random':
        await random(update=update, context=context, query=query)
    if query.data == 'random_by_author':
        await random_by_author(update=update, context=context, query=query)
        return TYPING_AUTHOR
    elif query.data == 'menu':
        await menu(update=update, context=context, query=query)
    elif query.data == 'start':
        await start(update=update, context=context, query=query)
    elif query.data == 'help':
        await help(update=update, context=context, query=query)


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    quote = get_random_quote()
    if query:
        await query.edit_message_text(text=quote)
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text=quote)


async def random_by_author(update: Update, context: ContextTypes.DEFAULT_TYPE, author=None, query=None):
    if query:
        await query.edit_message_text(text='Please enter author\'s name:')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Please enter author\'s name:')
    return TYPING_AUTHOR


async def typing_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    author = update.message.text
    quote = get_random_quote_by_author(author)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=quote)
    return ConversationHandler.END


async def typing_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

# If none of the above were provided
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I don't recognize this command.")
    
    
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Canceled.")
    return ConversationHandler.END


# LOGIC
def get_tags(message: str) -> list:
    """Returns a list of tags, similar to what the user provided in their message."""
    tags = ["Tag 1", "Tag 2", "Tag 3"]
    return tags


def get_random_quote() -> str:
    """Returns a random quote."""
    response = requests.get(API_URL + "/quotes/random")
    quote = '"' + response.json()[0]["content"] + '"'
    author = response.json()[0]["author"]

    return f"{quote}\n\n- {author}"


def get_random_quote_by_author(author: str) -> str:
    """Returns a random quote by a specific author."""
    author_format = author.capitalize().replace(" ", "-").replace(".", "")
    response = requests.get(API_URL + f"/quotes/random?author={author_format}")
    try:
        quote = '"' + response.json()[0]["content"] + '"'
        author_source = response.json()[0]["author"]
        return f"{quote}\n\n- {author_source}"
    except:
        return "I'm sorry, no quotes by this author were found."


def main() -> None:
    """Start the bot."""
    application = ApplicationBuilder().token('6973604569:AAH2NChCYageGr2sbm0mTfeKResrn5ePVxY').build()

    start_handler = CommandHandler('start', start)
    menu_handler = CommandHandler('menu', menu)
    random_handler = CommandHandler('random', random)
    random_by_author_handler = CommandHandler('random_by_author', random_by_author)
    help_handler = CommandHandler('help', help)
    cancel_handler = CommandHandler('cancel', cancel)
    author_handler = MessageHandler(filters.TEXT, typing_author)
    tag_handler = MessageHandler(filters.TEXT, typing_tag)
    unknown_handler = MessageHandler(filters.ALL, unknown)
    menu_buttons_handler = CallbackQueryHandler(menu_buttons)
    
    conv_handler = ConversationHandler(
        entry_points=[
            start_handler,
            random_by_author_handler,
            menu_buttons_handler
        ],
        states={
            TYPING_AUTHOR: [
                cancel_handler, 
                author_handler
            ]
        },
        fallbacks=[cancel_handler]
    )
    
    application.add_handlers([
        conv_handler,
        menu_buttons_handler,
        start_handler, 
        menu_handler,
        random_handler,
        random_by_author_handler,
        help_handler,
        unknown_handler
    ])
    
    application.run_polling()


if __name__ == '__main__':
    main()