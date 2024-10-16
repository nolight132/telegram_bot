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


API_URL = "https://johndturn-quotableapiproxy.web.val.run/"
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


def print_received_message(message: str):
    logger.info(f"Received a message: {message}")


def print_sent_message(message: str):
    logger.info(f"Sent a message: {message}")


# COMMANDS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    """Executes on /start."""
    logger.info(f"User {update.effective_chat.first_name} used /start command")
    message = "I am a bot, whose sole purpose is to send you quotes.\n\nAt the moment, only these commands are supported:" 
    if query:
        await query.edit_message_text(text=message, reply_markup=COMMANDS_KEYBOARD_MARKUP)
    else:
       await update.message.reply_text(text=message, reply_markup=COMMANDS_KEYBOARD_MARKUP)


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
        await query.edit_message_text(text='Please enter author\'s name:\n\n(/cancel to cancel)')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text='Please enter author\'s name:\n\n(/cancel to cancel)')
    return TYPING_AUTHOR


async def typing_author(update: Update, context: ContextTypes.DEFAULT_TYPE):
    author = update.message.text
    quote = get_random_quote_by_author(update, context, author)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=quote)
    return ConversationHandler.END


async def typing_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return ConversationHandler.END

# If none of the above were provided
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I don't recognize this command.")
    
    
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Canceled 👍")
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


def get_random_quote_by_author(update:Update, context:ContextTypes.DEFAULT_TYPE, author: str) -> str:
    """Returns a random quote by a specific author."""
    author_slug = to_slug(author)
    response = requests.get(API_URL + f"/quotes/random?author={author_slug}")
    try:
        quote = '"' + get_quote(response) + '"'
        author_source = get_author(response)
        return f"{quote}\n\n- {author_source}"
    except:
        try:
            response = requests.get(API_URL + f"/quotes/random?author='{autocorrect_author(author)}'")
            quote = '"' + get_quote(response) + '"'
            author_source = get_author(response)
            return f"{quote}\n\n- {author_source}"
        except:
            return "I'm sorry, no quotes by this author were found."


def to_slug(author_origin):
    print(author_origin.lower().replace(" ", "-").replace(".", ""))
    return author_origin.lower().replace(" ", "-").replace(".", "")


def autocorrect_author(author_origin):
    authors = []
    for i in range(1,requests.get(API_URL + "/authors?limit=150").json()["totalPages"] + 1):
        authors_list_response = requests.get(API_URL + f"/authors?page={i}&limit=150&sortBy=name")
        for author in authors_list_response.json()["results"]:
            authors.append(author["name"])
    for author_name in authors:
        if author_origin.lower() in author_name.lower(): 
            print(author_name)
            return author_name


def get_quote(response):
    return response.json()[0]["content"]


def get_author(response):
    return response.json()[0]["author"]


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