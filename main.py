import asyncio
import random
import json
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramForbiddenError

# ─── СЛОВА И ПОДСКАЗКИ ───────────────────────────────────────────────────────

WORDS = {
    "предметы": [
        "Стол", "Стул", "Ноутбук", "Чайник", "Кружка", "Зеркало", "Кровать", "Телевизор",
        "Холодильник", "Микроволновка", "Книга", "Ручка", "Карандаш", "Рюкзак", "Очки",
        "Часы", "Смартфон", "Наушники", "Клавиатура", "Мышка", "Ковер", "Диван",
        "Подушка", "Одеяло", "Шкаф", "Лампа", "Утюг", "Пылесос", "Стиральная машина", "Фен"
    ],
    "страны": [
        "Украина", "Чехия", "США", "Канада", "Великобритания", "Франция", "Германия",
        "Италия", "Испания", "Япония", "Китай", "Южная Корея", "Австралия", "Бразилия",
        "Аргентина", "Мексика", "Египет", "Турция", "Греция", "Швейцария", "Швеция",
        "Норвегия", "Финляндия", "Индия", "Таиланд", "Вьетнам", "Португалия", "Польша",
        "Австрия", "Нидерланды"
    ],
    "профессии": [
        "Программист", "Учитель", "Врач", "Повар", "Водитель", "Пилот", "Стюардесса",
        "Полицейский", "Пожарный", "Спасатель", "Актер", "Певец", "Музыкант", "Художник",
        "Писатель", "Журналист", "Фотограф", "Дизайнер", "Архитектор", "Инженер",
        "Строитель", "Электрик", "Сантехник", "Механик", "Фермер", "Продавец", "Кассир",
        "Официант", "Парикмахер", "Юрист"
    ],
    "знаменитости": [
        "Арсен Маркарян", "Эва Елфи", "Свити Фокс", "Павел Дуров", "Марк Цукерберг",
        "Илон Маск", "Дональд Трамп", "Владимир Зеленский", "Адольф Гитлер", "Иосиф Сталин"
    ]
}

SPY_HINTS = {
    "Канада":          ["холодный климат", "Северная Америка", "кленовый лист"],
    "Норвегия":        ["холодный климат", "фьорды", "Скандинавия"],
    "Финляндия":       ["холодный климат", "Скандинавия", "много озёр"],
    "Швеция":          ["холодный климат", "Скандинавия", "IKEA"],
    "Швейцария":       ["горы", "нейтральная страна", "шоколад и часы"],
    "Австрия":         ["горы", "Центральная Европа", "классическая музыка"],
    "Германия":        ["Европа", "автомобили", "пиво"],
    "Франция":         ["Европа", "мода и кухня", "Эйфелева башня"],
    "Италия":          ["Европа", "пицца и паста", "Колизей"],
    "Испания":         ["Европа", "жаркий климат", "фламенко"],
    "Португалия":      ["Европа", "океан", "пастель де ната"],
    "Великобритания":  ["острова", "Европа", "монархия"],
    "Нидерланды":      ["Европа", "тюльпаны", "велосипеды"],
    "Польша":          ["Восточная Европа", "пироги", "Варшава"],
    "Чехия":           ["Восточная Европа", "пиво", "Прага"],
    "Украина":         ["Восточная Европа", "подсолнухи", "борщ"],
    "Греция":          ["Средиземноморье", "древние руины", "оливки"],
    "Турция":          ["Азия и Европа", "Стамбул", "восточная кухня"],
    "Египет":          ["Африка", "пустыня", "пирамиды"],
    "Индия":           ["Азия", "специи", "Тадж-Махал"],
    "Китай":           ["Азия", "Великая стена", "очень много людей"],
    "Япония":          ["Азия", "аниме", "суши"],
    "Южная Корея":     ["Азия", "K-pop", "самсунг"],
    "Таиланд":         ["Азия", "тропики", "буддизм"],
    "Вьетнам":         ["Азия", "тропики", "фо бо"],
    "Австралия":       ["кенгуру", "Океания", "жаркий климат"],
    "Бразилия":        ["Южная Америка", "карнавал", "амазонка"],
    "Аргентина":       ["Южная Америка", "танго", "Месси"],
    "Мексика":         ["Северная Америка", "текила", "сомбреро"],
    "США":             ["Северная Америка", "Голливуд", "статуя Свободы"],
    "Стол":            ["мебель", "горизонтальная поверхность", "на нём едят или работают"],
    "Стул":            ["мебель", "сидят", "четыре ножки"],
    "Ноутбук":         ["электроника", "портативный компьютер", "экран и клавиатура"],
    "Чайник":          ["кухня", "кипятит воду", "электрический или обычный"],
    "Кружка":          ["кухня", "пьют горячее", "керамика или металл"],
    "Зеркало":         ["отражение", "стекло", "в ванной или прихожей"],
    "Кровать":         ["мебель", "спят", "подушки и матрас"],
    "Телевизор":       ["электроника", "смотрят фильмы", "экран на стене"],
    "Холодильник":     ["кухня", "хранит продукты", "холодный внутри"],
    "Микроволновка":   ["кухня", "разогревает еду", "кнопки и таймер"],
    "Книга":           ["чтение", "бумажные страницы", "есть автор"],
    "Ручка":           ["пишущий предмет", "чернила", "держат в руке"],
    "Карандаш":        ["пишущий предмет", "графит", "можно стереть резинкой"],
    "Рюкзак":          ["носят на спине", "для вещей", "у школьников всегда есть"],
    "Очки":            ["носят на носу", "для зрения или от солнца", "линзы"],
    "Часы":            ["показывают время", "носят на руке или вешают на стену", "стрелки или цифры"],
    "Смартфон":        ["электроника", "звонки и интернет", "сенсорный экран"],
    "Наушники":        ["электроника", "слушают музыку", "надевают на уши"],
    "Клавиатура":      ["ввод текста", "кнопки-клавиши", "к компьютеру"],
    "Мышка":           ["компьютерная периферия", "кликают кнопками", "двигают по столу"],
    "Ковер":           ["лежит на полу", "мягкий", "украшает комнату"],
    "Диван":           ["мебель", "сидят и лежат", "в гостиной"],
    "Подушка":         ["спят на ней", "мягкая", "на кровати или диване"],
    "Одеяло":          ["укрываются", "тёплое", "на кровати"],
    "Шкаф":            ["мебель", "хранят вещи", "с дверцами"],
    "Лампа":           ["освещение", "электрическая", "стоит или висит"],
    "Утюг":            ["гладит одежду", "горячий", "есть подошва"],
    "Пылесос":         ["убирает пыль", "всасывает мусор", "есть шланг"],
    "Стиральная машина": ["стирает одежду", "крутит бельё", "бытовая техника"],
    "Фен":             ["сушит волосы", "дует горячим воздухом", "в ванной"],
    "Программист":     ["сидит за компьютером", "пишет код", "IT-сфера"],
    "Учитель":         ["работает в школе", "объясняет материал", "ставит оценки"],
    "Врач":            ["лечит людей", "белый халат", "работает в больнице"],
    "Повар":           ["готовит еду", "работает на кухне", "нож и сковорода"],
    "Водитель":        ["управляет транспортом", "руль и педали", "возит людей или грузы"],
    "Пилот":           ["управляет самолётом", "кабина пилота", "форма и фуражка"],
    "Стюардесса":      ["на борту самолёта", "обслуживает пассажиров", "улыбается"],
    "Полицейский":     ["охраняет порядок", "форма и жетон", "есть дубинка или пистолет"],
    "Пожарный":        ["тушит пожары", "шлем и брандспойт", "красная машина"],
    "Спасатель":       ["спасает людей", "экстренные ситуации", "МЧС"],
    "Актер":           ["играет роли", "театр или кино", "знает текст наизусть"],
    "Певец":           ["поёт", "сцена и микрофон", "концерты"],
    "Музыкант":        ["играет на инструменте", "музыкальное выступление", "ноты"],
    "Художник":        ["рисует", "кисти и краски", "картины"],
    "Писатель":        ["пишет книги", "много читает", "придумывает истории"],
    "Журналист":       ["пишет статьи или снимает репортажи", "берёт интервью", "СМИ"],
    "Фотограф":        ["делает фотографии", "камера и объектив", "ловит момент"],
    "Дизайнер":        ["создаёт визуальные образы", "работает с формой и цветом", "компьютер или бумага"],
    "Архитектор":      ["проектирует здания", "чертежи", "смесь инженера и художника"],
    "Инженер":         ["проектирует и конструирует", "технические расчёты", "завод или офис"],
    "Строитель":       ["строит здания", "кирпичи и раствор", "каска на голове"],
    "Электрик":        ["работает с проводами", "чинит электрику", "нельзя касаться голыми руками"],
    "Сантехник":       ["чинит трубы", "работает с водой", "разводной ключ"],
    "Механик":         ["чинит машины", "гаечный ключ", "испачкан маслом"],
    "Фермер":          ["выращивает урожай или животных", "работает на земле", "рано встаёт"],
    "Продавец":        ["продаёт товары", "магазин или рынок", "общается с покупателями"],
    "Кассир":          ["пробивает товары", "касса и чеки", "сидит за прилавком"],
    "Официант":        ["обслуживает в кафе", "носит блюда", "принимает заказ"],
    "Парикмахер":      ["стрижёт волосы", "ножницы и расчёска", "в салоне"],
    "Юрист":           ["знает законы", "защищает в суде", "костюм и папка с документами"],
    "Арсен Маркарян":  ["украинский блогер", "известен в интернете", "молодой"],
    "Эва Елфи":        ["украинский блогер", "YouTube", "молодая"],
    "Свити Фокс":      ["украинский контент-мейкер", "в интернете", "популярный"],
    "Павел Дуров":     ["основатель Telegram", "IT-предприниматель", "живёт за рубежом"],
    "Марк Цукерберг":  ["основатель Facebook", "миллиардер", "IT-сфера"],
    "Илон Маск":       ["Tesla и SpaceX", "миллиардер", "часто в новостях"],
    "Дональд Трамп":   ["политик", "США", "президент"],
    "Владимир Зеленский": ["президент Украины", "бывший актёр", "политик"],
    "Адольф Гитлер":   ["исторический злодей", "Вторая мировая", "диктатор"],
    "Иосиф Сталин":    ["исторический лидер СССР", "диктатор", "репрессии"],
}

THINK_TIME = 30
ROUNDS_BEFORE_VOTE = 2
MAX_CONSECUTIVE_SKIPS = 2

# ─── ТОКЕН: читаем из переменной окружения (для Render) ─────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")

# ─── ОЧКИ ────────────────────────────────────────────────────────────────────
POINTS_SPY_WIN       =  16
POINTS_SPY_LOSE      =  -5
POINTS_CIVILIAN_WIN  =   8
POINTS_CIVILIAN_LOSE =  -3
POINTS_DRAW          =  -1
POINTS_AFK_KICK      =  -4

RATINGS_FILE = "ratings.json"


# ─── РЕЙТИНГ ─────────────────────────────────────────────────────────────────

def load_ratings() -> dict:
    if os.path.exists(RATINGS_FILE):
        with open(RATINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_ratings(ratings: dict):
    with open(RATINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(ratings, f, ensure_ascii=False, indent=2)


def add_points(ratings: dict, chat_id: int, user_id: int, name: str, points: int):
    cid = str(chat_id)
    uid = str(user_id)
    if cid not in ratings:
        ratings[cid] = {}
    if uid not in ratings[cid]:
        ratings[cid][uid] = {"name": name, "points": 0}
    ratings[cid][uid]["name"] = name
    ratings[cid][uid]["points"] += points


def get_spy_hint(word: str) -> str:
    hints = SPY_HINTS.get(word)
    if hints:
        return random.choice(hints)
    return "подсказка недоступна"


# ─── БОТ И ДИСПЕТЧЕР ────────────────────────────────────────────────────────

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
games = {}


# ─── ГЕНЕРАЦИЯ РОЛЕЙ ────────────────────────────────────────────────────────

def generate_roles(players, theme):
    chance = random.random()

    if chance <= 0.10 and len(players) >= 4:
        spy_players = random.sample(players, 2)
        word = random.choice(WORDS[theme])
        roles = {
            p['id']: ("ШПИОН", None) if p in spy_players else ("МИРНЫЙ", word)
            for p in players
        }
        spy_ids = [p['id'] for p in spy_players]
        mode_text = "⚠️ В этом раунде может быть больше одного шпиона..."
        game_mode = "double_spy"

    elif 0.10 < chance <= 0.20:
        main_word = random.choice(WORDS[theme])
        alt_words = [w for w in WORDS[theme] if w != main_word]
        alt_word = random.choice(alt_words) if alt_words else main_word
        imposter = random.choice(players)
        roles = {}
        for p in players:
            roles[p['id']] = ("МИРНЫЙ", alt_word if p == imposter else main_word)
        spy_ids = []
        mode_text = "🧐 Что-то в этом раунде не так... (Без шпиона?)"
        game_mode = "no_spy"

    else:
        spy_player = random.choice(players)
        word = random.choice(WORDS[theme])
        roles = {
            p['id']: ("ШПИОН", None) if p == spy_player else ("МИРНЫЙ", word)
            for p in players
        }
        spy_ids = [spy_player['id']]
        mode_text = "🕵️ Шпион среди нас..."
        game_mode = "normal"

    return roles, spy_ids, mode_text, game_mode


# ─── ТАЙМЕР ──────────────────────────────────────────────────────────────────

async def cancel_timer(game):
    task = game.get('timer_task')
    if task and not task.done():
        task.cancel()
    game['timer_task'] = None


async def start_turn_timer(chat_id: int):
    game = games.get(chat_id)
    if not game:
        return

    current_player = game['players'][game['turn_index']]
    player_name = current_player['name']

    await bot.send_message(chat_id, f"⏳ {player_name}, у вас {THINK_TIME} секунд на ответ...")
    await asyncio.sleep(THINK_TIME)

    game = games.get(chat_id)
    if not game or game['status'] != 'playing':
        return
    if game['players'][game['turn_index']]['id'] != current_player['id']:
        return

    player_id = current_player['id']
    skip_counts = game.setdefault('skip_counts', {})
    skip_counts[player_id] = skip_counts.get(player_id, 0) + 1

    if skip_counts[player_id] >= MAX_CONSECUTIVE_SKIPS:
        await bot.send_message(
            chat_id,
            f"🚫 {player_name} не отвечал {MAX_CONSECUTIVE_SKIPS} хода подряд и исключён из игры!"
        )
        ratings = load_ratings()
        add_points(ratings, chat_id, player_id, player_name, POINTS_AFK_KICK)
        save_ratings(ratings)
        await bot.send_message(chat_id, f"📉 {player_name}: {POINTS_AFK_KICK} очков за AFK.")

        game['players'] = [p for p in game['players'] if p['id'] != player_id]
        del skip_counts[player_id]

        if len(game['players']) < 2:
            await bot.send_message(chat_id, "❌ Недостаточно игроков. Игра завершена.\n\n🔁 Напишите /spy чтобы начать снова.")
            del games[chat_id]
            return

        game['turn_index'] = game['turn_index'] % len(game['players'])
        await advance_turn(chat_id, skip_kicked=True)
    else:
        await bot.send_message(chat_id, f"⌛ Время вышло! {player_name} пропускает ход.")
        await advance_turn(chat_id)


async def advance_turn(chat_id: int, skip_kicked: bool = False):
    game = games.get(chat_id)
    if not game:
        return

    if not skip_kicked:
        game['turn_index'] += 1

    if game['turn_index'] < len(game['players']):
        next_player = game['players'][game['turn_index']]['name']
        await bot.send_message(chat_id, f"🗣 Следующим говорит: {next_player}")
        task = asyncio.create_task(start_turn_timer(chat_id))
        game['timer_task'] = task
    else:
        game['round_number'] = game.get('round_number', 0) + 1
        rn = game['round_number']

        if rn < ROUNDS_BEFORE_VOTE:
            rounds_left = ROUNDS_BEFORE_VOTE - rn
            game['turn_index'] = 0
            game['status'] = 'playing'
            random.shuffle(game['players'])
            first_player = game['players'][0]['name']
            await bot.send_message(
                chat_id,
                f"✅ Раунд {rn} завершён! До голосования: {rounds_left} круг(а).\n\n🗣 Первым говорит: {first_player}"
            )
            task = asyncio.create_task(start_turn_timer(chat_id))
            game['timer_task'] = task
        else:
            game['status'] = 'voting_decision'
            await bot.send_message(
                chat_id,
                f"✅ Раунд {rn} завершён! Все {ROUNDS_BEFORE_VOTE} круга пройдены. Что делаем дальше?",
                reply_markup=get_vote_kb()
            )


# ─── КЛАВИАТУРЫ ─────────────────────────────────────────────────────────────

def get_player_count_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="3 игрока", callback_data="size_3"),
         InlineKeyboardButton(text="4 игрока", callback_data="size_4")]
    ])

def get_join_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✋ Участвовать", callback_data="join_game")]
    ])

def get_themes_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Предметы", callback_data="theme_предметы"),
         InlineKeyboardButton(text="Страны", callback_data="theme_страны")],
        [InlineKeyboardButton(text="Профессии", callback_data="theme_профессии"),
         InlineKeyboardButton(text="Знаменитости", callback_data="theme_знаменитости")]
    ])

def get_vote_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗳 Голосовать", callback_data="vote_start"),
         InlineKeyboardButton(text="▶️ Ещё круг", callback_data="vote_skip")]
    ])

def get_vote_players_kb(players):
    buttons = [[InlineKeyboardButton(text=p['name'], callback_data=f"vote_player_{p['id']}")] for p in players]
    buttons.append([InlineKeyboardButton(text="❌ Воздержаться", callback_data="vote_abstain")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── ХЭНДЛЕРЫ КОМАНД ────────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.chat.type == "private":
        await message.answer(
            "👋 Привет! Теперь я смогу присылать тебе секретные слова и роли, "
            "когда мы будем играть в группах.\n\nЧтобы начать игру — напиши /spy в группе!"
        )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "🕵️‍♂️ <b>Шпион — правила игры</b>\n\n"
        "<b>Цель игры:</b>\n"
        "• <b>Мирные</b> должны вычислить шпиона и проголосовать против него.\n"
        "• <b>Шпион</b> должен остаться незамеченным и угадать секретное слово.\n\n"
        "<b>Как играть:</b>\n"
        "1️⃣ Создатель пишет /spy в группе и выбирает количество игроков.\n"
        "2️⃣ Все нажимают <b>✋ Участвовать</b>.\n"
        "3️⃣ Создатель выбирает тему.\n"
        "4️⃣ Каждый получает роль в личные сообщения:\n"
        "   — Мирный видит <b>слово</b>\n"
        "   — Шпион видит только <b>тему</b> и <b>подсказку</b>\n"
        "5️⃣ По очереди каждый игрок говорит одну фразу или слово, связанное с темой.\n"
        f"6️⃣ После <b>{ROUNDS_BEFORE_VOTE} кругов</b> можно проголосовать или продолжить.\n"
        "7️⃣ Если шпион пойман — мирные побеждают. Если нет — шпион!\n\n"
        f"<b>⚠️ AFK:</b> Если игрок пропускает {MAX_CONSECUTIVE_SKIPS} хода подряд — он исключается "
        f"и получает {POINTS_AFK_KICK} очков.\n\n"
        "<b>Особые режимы:</b>\n"
        "⚠️ <b>Два шпиона</b> — редкий шанс, что в игре сразу двое шпионов.\n"
        "🧐 <b>Без шпиона</b> — один игрок получает другое слово из той же темы.\n\n"
        "<b>Очки:</b>\n"
        f"🏆 Шпион победил: +{POINTS_SPY_WIN}\n"
        f"☠️ Шпион пойман: {POINTS_SPY_LOSE}\n"
        f"🎉 Мирный победил: +{POINTS_CIVILIAN_WIN}\n"
        f"😔 Мирный проиграл: {POINTS_CIVILIAN_LOSE}\n"
        f"🤝 Ничья: {POINTS_DRAW} (все)\n"
        f"💤 AFK кик: {POINTS_AFK_KICK}\n\n"
        "<b>Команды:</b>\n"
        "/spy — начать новую игру\n"
        "/leaderboard — рейтинг группы\n"
        "/help — это сообщение"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("spy"))
async def cmd_spy(message: types.Message):
    if message.chat.type == "private":
        await message.answer("Эту команду нужно использовать в группе!")
        return

    chat_id = message.chat.id
    games[chat_id] = {
        'creator': message.from_user.id,
        'status': 'setup',
        'players': [],
        'turn_index': 0,
        'timer_task': None,
        'votes': {},
        'spy_ids': [],
        'game_mode': 'normal',
        'round_number': 0,
        'theme': None,
        'word': None,
        'skip_counts': {},
    }
    await message.answer(
        "🕵️‍♂️ Начинаем игру в Шпиона!\nСоздатель, выберите количество игроков:",
        reply_markup=get_player_count_kb()
    )


@dp.message(Command("leaderboard"))
async def leaderboard(message: types.Message):
    if message.chat.type == "private":
        await message.answer("Эта команда работает только в группах!")
        return

    chat_id = message.chat.id
    ratings = load_ratings()
    cid = str(chat_id)

    if cid not in ratings or not ratings[cid]:
        await message.answer("📊 В этой группе ещё никто не играл!")
        return

    group_data = ratings[cid]
    sorted_players = sorted(group_data.values(), key=lambda x: x['points'], reverse=True)

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Топ игроков группы:</b>\n"]
    for i, player in enumerate(sorted_players[:10]):
        medal = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{medal} {player['name']} — <b>{player['points']}</b> очков")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ─── ЛОББИ И СТАРТ ИГРЫ ─────────────────────────────────────────────────────

@dp.callback_query(F.data.startswith("size_"))
async def select_size(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    game = games.get(chat_id)

    if not game or game['creator'] != callback.from_user.id:
        await callback.answer("Только создатель игры может выбирать!", show_alert=True)
        return

    size = int(callback.data.split("_")[1])
    game['max_players'] = size
    game['status'] = 'lobby'

    await callback.message.edit_text(
        f"🕵️‍♂️ Игра создана на {size} человек!\nНажмите кнопку ниже, чтобы присоединиться.\nУчастников: 0/{size}",
        reply_markup=get_join_kb()
    )


@dp.callback_query(F.data == "join_game")
async def join_game(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    game = games.get(chat_id)

    if not game or game['status'] != 'lobby':
        await callback.answer("Игра не в стадии набора!", show_alert=True)
        return

    user_id = callback.from_user.id
    if any(p['id'] == user_id for p in game['players']):
        await callback.answer("Вы уже в игре!", show_alert=True)
        return

    game['players'].append({'id': user_id, 'name': callback.from_user.first_name})
    current_count = len(game['players'])

    if current_count < game['max_players']:
        await callback.message.edit_text(
            f"🕵️‍♂️ Игра создана на {game['max_players']} человек!\nНажмите кнопку ниже, чтобы присоединиться.\nУчастников: {current_count}/{game['max_players']}",
            reply_markup=get_join_kb()
        )
    else:
        game['status'] = 'theme_selection'
        await callback.message.edit_text(
            "✅ Лобби заполнено!\nСоздатель игры, выберите тему:",
            reply_markup=get_themes_kb()
        )


@dp.callback_query(F.data.startswith("theme_"))
async def select_theme(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    game = games.get(chat_id)

    if not game or game['creator'] != callback.from_user.id:
        await callback.answer("Только создатель может выбирать тему!", show_alert=True)
        return

    theme = callback.data.split("_")[1]
    game['theme'] = theme
    roles_map, spy_ids, mode_info, game_mode = generate_roles(game['players'], theme)
    game['status'] = 'playing'
    game['spy_ids'] = spy_ids
    game['game_mode'] = game_mode
    game['round_number'] = 0
    game['skip_counts'] = {}
    random.shuffle(game['players'])

    spy_word = None
    for player in game['players']:
        role, word = roles_map[player['id']]
        if role == "МИРНЫЙ":
            spy_word = word
            break
    game['word'] = spy_word

    failed_users = []
    for player in game['players']:
        role, word = roles_map[player['id']]
        try:
            if role == "ШПИОН":
                hint = get_spy_hint(spy_word) if spy_word else "подсказка недоступна"
                await bot.send_message(
                    player['id'],
                    f"🕵️‍♂️ Вы <b>ШПИОН</b>!\n"
                    f"Тема: <b>{theme}</b>\n"
                    f"💡 Подсказка: <i>{hint}</i>\n\n"
                    f"Постарайтесь угадать слово и остаться незамеченным!",
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    player['id'],
                    f"🤫 Вы <b>мирный</b>.\n"
                    f"Тема: <b>{theme}</b>\n"
                    f"Слово: <b>{word}</b>\n\n"
                    f"Найдите шпиона!",
                    parse_mode="HTML"
                )
        except TelegramForbiddenError:
            failed_users.append(player['name'])

    if failed_users:
        await callback.message.answer(f"❌ Игроки {', '.join(failed_users)} не запустили бота в ЛС!")
        del games[chat_id]
        return

    first_player = game['players'][0]['name']
    await callback.message.edit_text(
        f"🎮 Игра началась!\n{mode_info}\n\n"
        f"Голосование появится после {ROUNDS_BEFORE_VOTE} кругов.\n\n"
        f"🗣 Первым высказывается: <b>{first_player}</b>",
        parse_mode="HTML"
    )

    task = asyncio.create_task(start_turn_timer(chat_id))
    game['timer_task'] = task


# ─── ГОЛОСОВАНИЕ ─────────────────────────────────────────────────────────────

@dp.callback_query(F.data == "vote_start")
async def vote_start(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    game = games.get(chat_id)

    if not game or game['status'] != 'voting_decision':
        await callback.answer("Голосование сейчас недоступно.", show_alert=True)
        return

    game['status'] = 'voting'
    game['votes'] = {}

    players_list = "\n".join(f"• {p['name']}" for p in game['players'])
    await callback.message.edit_text(
        f"🗳 Голосование началось!\nКаждый игрок голосует за подозреваемого шпиона.\n\nИгроки:\n{players_list}",
        reply_markup=get_vote_players_kb(game['players'])
    )
    await callback.answer()


@dp.callback_query(F.data == "vote_skip")
async def vote_skip(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    game = games.get(chat_id)

    if not game or game['status'] != 'voting_decision':
        await callback.answer("Пропуск сейчас недоступен.", show_alert=True)
        return

    game['round_number'] = 0
    game['turn_index'] = 0
    game['status'] = 'playing'
    game['skip_counts'] = {}
    random.shuffle(game['players'])

    first_player = game['players'][0]['name']
    await callback.message.edit_text(
        f"▶️ Голосование пропущено. Начинаем новую серию кругов!\n\n🗣 Первым говорит: {first_player}"
    )

    task = asyncio.create_task(start_turn_timer(chat_id))
    game['timer_task'] = task
    await callback.answer()


@dp.callback_query(F.data.startswith("vote_player_") | (F.data == "vote_abstain"))
async def process_vote(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    game = games.get(chat_id)

    if not game or game['status'] != 'voting':
        await callback.answer("Голосование не идёт.", show_alert=True)
        return

    voter_id = callback.from_user.id

    if not any(p['id'] == voter_id for p in game['players']):
        await callback.answer("Вы не участвуете в игре!", show_alert=True)
        return

    if voter_id in game['votes']:
        await callback.answer("Вы уже проголосовали!", show_alert=True)
        return

    if callback.data == "vote_abstain":
        game['votes'][voter_id] = None
        await callback.answer("Вы воздержались.")
    else:
        voted_id = int(callback.data.split("_")[2])
        game['votes'][voter_id] = voted_id
        voted_name = next((p['name'] for p in game['players'] if p['id'] == voted_id), "?")
        await callback.answer(f"Вы проголосовали за {voted_name}.")

    if len(game['votes']) >= len(game['players']):
        await finish_voting(chat_id, callback.message)


async def finish_voting(chat_id: int, message: types.Message):
    game = games.get(chat_id)
    if not game:
        return

    vote_count = {}
    for voted_id in game['votes'].values():
        if voted_id is not None:
            vote_count[voted_id] = vote_count.get(voted_id, 0) + 1

    result_lines = ["📊 Результаты голосования:"]
    for player in game['players']:
        count = vote_count.get(player['id'], 0)
        result_lines.append(f"• {player['name']}: {count} голос(ов)")

    ratings = load_ratings()
    game_mode = game.get('game_mode', 'normal')
    spy_ids = game.get('spy_ids', [])
    spy_names = [p['name'] for p in game['players'] if p['id'] in spy_ids]
    secret_word = game.get('word')

    eliminated_id = None
    spy_won = False
    is_draw = False

    if vote_count:
        max_votes = max(vote_count.values())
        top = [pid for pid, v in vote_count.items() if v == max_votes]

        if len(top) == 1:
            eliminated_id = top[0]
            eliminated_name = next(p['name'] for p in game['players'] if p['id'] == eliminated_id)
            result_lines.append(f"\n☠️ Большинство проголосовало за: <b>{eliminated_name}</b>")

            if game_mode == "double_spy":
                result_lines.append(f"🕵️🕵️ Шпионами были: <b>{' и '.join(spy_names)}</b>")
                if eliminated_id in spy_ids:
                    result_lines.append("✅ Один из шпионов пойман! Мирные победили! 🎉")
                    spy_won = False
                else:
                    result_lines.append("❌ Мирный выбыл! Оба шпиона победили! 🕵️🕵️")
                    spy_won = True

            elif game_mode == "no_spy":
                result_lines.append("🎭 Это был <b>особый раунд</b> — настоящих шпионов не было!")
                result_lines.append(f"Один игрок получил другое слово из той же темы. Выбыл мирный: <b>{eliminated_name}</b>.")
                result_lines.append("Очки за этот раунд не начисляются.")
                spy_won = False

            else:
                result_lines.append(f"🕵️ Шпионом был: <b>{spy_names[0] if spy_names else '?'}</b>")
                if eliminated_id in spy_ids:
                    result_lines.append("✅ Шпион пойман! Мирные победили! 🎉")
                    spy_won = False
                else:
                    result_lines.append("❌ Это был мирный! Шпион победил! 🕵️")
                    spy_won = True
        else:
            is_draw = True
            result_lines.append("\n🤝 Ничья! Никто не выбывает. Все получают -1 очко.")
            if spy_names:
                result_lines.append(f"🕵️ Шпионом(и) был(и): <b>{', '.join(spy_names)}</b>")
    else:
        result_lines.append("\nВсе воздержались — никто не выбывает.")
        if spy_names:
            result_lines.append(f"🕵️ Шпионом(и) был(и): <b>{', '.join(spy_names)}</b>")

    if secret_word:
        result_lines.append(f"\n🔑 Секретное слово было: <b>{secret_word}</b>")

    if game_mode != "no_spy":
        points_lines = ["\n🏅 Очки за раунд:"]
        for player in game['players']:
            is_spy = player['id'] in spy_ids

            if is_draw:
                pts = POINTS_DRAW
                label = f"{'+' if pts > 0 else ''}{pts} (ничья 🤝)"
            elif is_spy:
                pts = POINTS_SPY_WIN if spy_won else POINTS_SPY_LOSE
                label = f"{'+' if pts > 0 else ''}{pts} (шпион {'победил 🏆' if spy_won else 'пойман ☠️'})"
            else:
                pts = POINTS_CIVILIAN_WIN if not spy_won else POINTS_CIVILIAN_LOSE
                label = f"{'+' if pts > 0 else ''}{pts} (мирный {'победил 🎉' if not spy_won else 'проиграл 😔'})"

            add_points(ratings, chat_id, player['id'], player['name'], pts)
            points_lines.append(f"• {player['name']}: {label}")

        save_ratings(ratings)
        result_lines.extend(points_lines)
        result_lines.append("\n📊 /leaderboard — рейтинг группы")

    result_lines.append("\n🔁 Хотите сыграть ещё? Напишите /spy")
    del games[chat_id]

    await message.edit_text("\n".join(result_lines), parse_mode="HTML")


# ─── ХОДЫ ИГРОКОВ ────────────────────────────────────────────────────────────

@dp.message()
async def handle_turns(message: types.Message):
    chat_id = message.chat.id
    game = games.get(chat_id)

    if not game or game['status'] != 'playing':
        return

    current_player = game['players'][game['turn_index']]
    if message.from_user.id != current_player['id']:
        return

    game.setdefault('skip_counts', {})[current_player['id']] = 0
    await cancel_timer(game)
    await advance_turn(chat_id)


# ─── ВЕБ-СЕРВЕР (для Render) ─────────────────────────────────────────────────

async def health_handler(request):
    return web.Response(text="I am alive")

async def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"✅ Web server started on port {port}")


# ─── ЗАПУСК ──────────────────────────────────────────────────────────────────

async def main():
    await asyncio.gather(
        run_web_server(),
        dp.start_polling(bot),
    )

if __name__ == "__main__":
    asyncio.run(main())