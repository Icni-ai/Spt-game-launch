import asyncio
import random
import json
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramForbiddenError

# ─── СЛОВА ───────────────────────────────────────────────────────────────────

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
        "Илон Маск", "Дональд Трамп", "Владимир Зеленский", "Адольф Гитлер", "Иосиф Сталин",
        "Майк Тайсон", "Александр Усик", "Джеффри Эпштейн", "Альберт Эйнштейн",
        "Криштиану Роналду", "Лионель Месси", "Килиан Мбаппе", "Исаак Ньютон",
        "Наполеон Бонапарт", "Владимир Путин", "Майкл Джексон", "Брайан Крэнстон",
        "Леонардо ДиКаприо", "Брэд Питт", "Райан Гослинг",
        "Ислам Махачев", "Хабиб Нурмагомедов", "Иван Золо"
    ]
}

# ─── ПОДСКАЗКИ ───────────────────────────────────────────────────────────────
# Принцип: подсказки намекают на категорию/свойство, но не раскрывают слово напрямую

SPY_HINTS = {
    # ── СТРАНЫ: Европа ──
    "Украина":         ["в Европе", "есть выход к морю", "пшеничные поля"],
    "Чехия":           ["в Европе", "без выхода к морю", "средних размеров страна"],
    "Великобритания":  ["в Европе", "острова", "монархия"],
    "Франция":         ["в Европе", "граничит с несколькими странами", "романские языки"],
    "Германия":        ["в Европе", "крупная страна", "промышленная держава"],
    "Италия":          ["в Европе", "похожа на сапог", "средиземноморье"],
    "Испания":         ["в Европе", "на полуострове", "средиземноморье"],
    "Португалия":      ["в Европе", "на полуострове", "выход к океану"],
    "Польша":          ["в Восточной Европе", "большая страна", "граничит с Германией"],
    "Австрия":         ["в Центральной Европе", "горная страна", "небольшая"],
    "Швейцария":       ["в Центральной Европе", "горная страна", "нейтральная"],
    "Нидерланды":      ["в Западной Европе", "низинная страна", "небольшая"],
    "Греция":          ["в Южной Европе", "много островов", "средиземноморье"],
    "Швеция":          ["в Северной Европе", "большая страна", "Скандинавия"],
    "Норвегия":        ["в Северной Европе", "длинная береговая линия", "Скандинавия"],
    "Финляндия":       ["в Северной Европе", "граничит с Россией", "Скандинавия"],
    "Турция":          ["частично в Европе", "частично в Азии", "большая страна"],

    # ── СТРАНЫ: Азия ──
    "Япония":          ["в Азии", "островное государство", "высокие технологии"],
    "Китай":           ["в Азии", "одна из крупнейших стран", "много населения"],
    "Южная Корея":     ["в Азии", "полуостров", "развитая экономика"],
    "Индия":           ["в Азии", "очень большая страна", "много населения"],
    "Таиланд":         ["в Азии", "тропический климат", "популярен у туристов"],
    "Вьетнам":         ["в Азии", "тропический климат", "вытянутая форма"],

    # ── СТРАНЫ: Другие континенты ──
    "США":             ["в Северной Америке", "большая страна", "федерация штатов"],
    "Канада":          ["в Северной Америке", "очень большая страна", "холодный север"],
    "Мексика":         ["в Северной Америке", "граничит с США", "испанский язык"],
    "Бразилия":        ["в Южной Америке", "крупнейшая страна континента", "тропический климат"],
    "Аргентина":       ["в Южной Америке", "на юге континента", "испанский язык"],
    "Австралия":       ["отдельный континент", "в южном полушарии", "омывается двумя океанами"],
    "Египет":          ["в Африке", "частично в Азии", "пустынный климат"],

    # ── ПРЕДМЕТЫ: материал/цвет/форма ──
    "Стол":            ["бывает деревянным или металлическим", "прямоугольный чаще всего", "есть ножки"],
    "Стул":            ["бывает деревянным или пластиковым", "небольшой размер", "есть спинка"],
    "Ноутбук":         ["прямоугольный", "бывает чёрным или серым", "лёгкий"],
    "Чайник":          ["бывает металлическим или пластиковым", "есть ручка", "небольшой"],
    "Кружка":          ["бывает керамической", "круглая", "небольшая"],
    "Зеркало":         ["гладкая поверхность", "бывает прямоугольным или круглым", "блестит"],
    "Кровать":         ["большая мебель", "прямоугольная", "мягкая поверхность"],
    "Телевизор":       ["прямоугольный", "плоский", "бывает чёрным"],
    "Холодильник":     ["прямоугольный", "обычно белый или серый", "высокий"],
    "Микроволновка":   ["прямоугольная коробка", "бывает белой или серебристой", "небольшая"],
    "Книга":           ["прямоугольная", "бывает разных размеров", "мягкая или твёрдая обложка"],
    "Ручка":           ["длинная и тонкая", "бывает синей или чёрной", "лёгкая"],
    "Карандаш":        ["длинный и тонкий", "бывает жёлтым", "деревянный"],
    "Рюкзак":          ["бывает разных цветов", "мягкий", "есть лямки"],
    "Очки":            ["прозрачные линзы", "металлическая или пластиковая оправа", "небольшие"],
    "Часы":            ["бывают круглыми", "бывают металлическими или пластиковыми", "небольшие"],
    "Смартфон":        ["прямоугольный", "плоский", "стеклянный экран"],
    "Наушники":        ["бывают белыми или чёрными", "мягкие накладки", "есть провод или нет"],
    "Клавиатура":      ["прямоугольная", "плоская", "много кнопок"],
    "Мышка":           ["небольшая", "бывает чёрной или белой", "гладкая"],
    "Ковер":           ["плоский", "мягкий", "бывает разных цветов и узоров"],
    "Диван":           ["большая мягкая мебель", "бывает разных цветов", "горизонтальный"],
    "Подушка":         ["мягкая", "бывает белой", "квадратная или прямоугольная"],
    "Одеяло":          ["мягкое", "бывает разных цветов", "прямоугольное"],
    "Шкаф":            ["большая мебель", "прямоугольный", "бывает деревянным"],
    "Лампа":           ["бывает белой или металлической", "есть провод", "разные формы"],
    "Утюг":            ["металлическая подошва", "бывает белым или серым", "треугольная форма"],
    "Пылесос":         ["бывает разных цветов", "есть длинный шланг", "на колёсиках"],
    "Стиральная машина": ["белая чаще всего", "круглый люк", "большая"],
    "Фен":             ["пластиковый", "бывает чёрным или белым", "есть ручка"],

    # ── ПРОФЕССИИ ──
    "Программист":     ["офисная работа", "нужен компьютер", "умственный труд"],
    "Учитель":         ["работа с людьми", "нужно образование", "умственный труд"],
    "Врач":            ["нужна специальная форма", "работа с людьми", "нужно образование"],
    "Повар":           ["работа на кухне", "физический труд", "нужен инвентарь"],
    "Водитель":        ["нужны права", "физический труд", "работа с транспортом"],
    "Пилот":           ["нужно специальное образование", "работа с транспортом", "высокая ответственность"],
    "Стюардесса":      ["работа с людьми", "нужна специальная форма", "связана с авиацией"],
    "Полицейский":     ["нужна специальная форма", "работа с людьми", "государственная служба"],
    "Пожарный":        ["нужна специальная форма", "физический труд", "опасная работа"],
    "Спасатель":       ["физический труд", "опасная работа", "государственная служба"],
    "Актер":           ["творческая работа", "работа с людьми", "нужен талант"],
    "Певец":           ["творческая работа", "нужен талант", "публичная профессия"],
    "Музыкант":        ["творческая работа", "нужен талант", "нужен инструмент"],
    "Художник":        ["творческая работа", "нужен инвентарь", "умственный труд"],
    "Писатель":        ["творческая работа", "нужен компьютер или бумага", "умственный труд"],
    "Журналист":       ["работа с людьми", "нужен компьютер", "публичная профессия"],
    "Фотограф":        ["нужен инвентарь", "творческая работа", "бывает на улице"],
    "Дизайнер":        ["творческая работа", "нужен компьютер", "умственный труд"],
    "Архитектор":      ["нужно образование", "умственный труд", "творческая работа"],
    "Инженер":         ["нужно образование", "умственный труд", "технические знания"],
    "Строитель":       ["физический труд", "работа на улице", "нужен инвентарь"],
    "Электрик":        ["физический труд", "нужен инвентарь", "опасная работа"],
    "Сантехник":       ["физический труд", "нужен инвентарь", "работа в помещении"],
    "Механик":         ["физический труд", "нужен инвентарь", "работа с техникой"],
    "Фермер":          ["физический труд", "работа на улице", "зависит от погоды"],
    "Продавец":        ["работа с людьми", "физический труд", "нужна касса"],
    "Кассир":          ["работа с людьми", "сидячая работа", "нужна касса"],
    "Официант":        ["работа с людьми", "физический труд", "нужна форма"],
    "Парикмахер":      ["работа с людьми", "нужен инвентарь", "творческая работа"],
    "Юрист":           ["нужно образование", "работа с людьми", "офисная работа"],

    # ── ЗНАМЕНИТОСТИ: украинские блогеры ──
    "Арсен Маркарян":  ["публичная личность", "молодой", "украинец"],
    "Эва Елфи":        ["публичная личность", "молодая", "украинка"],
    "Свити Фокс":      ["публичная личность", "украинец", "интернет"],
    "Иван Золо":       ["публичная личность", "украинец", "молодой"],

    # ── ЗНАМЕНИТОСТИ: IT/бизнес ──
    "Павел Дуров":     ["бизнесмен", "живёт за рубежом", "связан с IT"],
    "Марк Цукерберг":  ["бизнесмен", "американец", "связан с IT"],
    "Илон Маск":       ["бизнесмен", "американец", "связан с техникой"],

    # ── ЗНАМЕНИТОСТИ: политика ──
    "Дональд Трамп":   ["политик", "американец", "пожилой"],
    "Владимир Зеленский": ["политик", "украинец", "публичная личность"],
    "Владимир Путин":  ["политик", "россиянин", "пожилой"],
    "Наполеон Бонапарт": ["исторический деятель", "политик", "военный"],
    "Адольф Гитлер":   ["исторический деятель", "политик", "злодей"],
    "Иосиф Сталин":    ["исторический деятель", "политик", "диктатор"],
    "Джеффри Эпштейн": ["американец", "скандальная личность", "преступник"],

    # ── ЗНАМЕНИТОСТИ: спорт ──
    "Майк Тайсон":     ["спортсмен", "американец", "боевые искусства"],
    "Александр Усик":  ["спортсмен", "украинец", "боевые искусства"],
    "Криштиану Роналду": ["спортсмен", "европеец", "командный спорт"],
    "Лионель Месси":   ["спортсмен", "южноамериканец", "командный спорт"],
    "Килиан Мбаппе":   ["спортсмен", "европеец", "командный спорт"],
    "Ислам Махачев":   ["спортсмен", "россиянин", "боевые искусства"],
    "Хабиб Нурмагомедов": ["спортсмен", "россиянин", "боевые искусства"],

    # ── ЗНАМЕНИТОСТИ: наука/искусство ──
    "Альберт Эйнштейн": ["учёный", "исторический деятель", "немец"],
    "Исаак Ньютон":    ["учёный", "исторический деятель", "британец"],
    "Майкл Джексон":   ["артист", "американец", "певец"],
    "Брайан Крэнстон": ["артист", "американец", "актёр"],
    "Леонардо ДиКаприо": ["артист", "американец", "актёр"],
    "Брэд Питт":       ["артист", "американец", "актёр"],
    "Райан Гослинг":   ["артист", "канадец", "актёр"],
}

# ─── ВОПРОСЫ ДЛЯ РЕЖИМА ВОПРОСОВ ─────────────────────────────────────────────

QUESTIONS = [
    "Какого это цвета?",
    "Где вы это встречали?",
    "Как это можно использовать?",
    "Это большое или маленькое?",
    "Это живое или нет?",
    "Это дорогое или дешёвое?",
    "Это бывает на улице или в помещении?",
    "Это твёрдое или мягкое?",
    "С чем это ассоциируется?",
    "Когда вы последний раз с этим сталкивались?",
    "Это приятное или нет?",
    "Это бывает у всех или только у некоторых?",
    "Это старое или современное?",
    "Это можно потрогать?",
    "Это связано с работой или отдыхом?",
]

THINK_TIME = 30
ROUNDS_BEFORE_VOTE = 2
MAX_CONSECUTIVE_SKIPS = 2

BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")

# ─── ОЧКИ ────────────────────────────────────────────────────────────────────
POINTS_SPY_WIN          =  16
POINTS_SPY_LOSE         =  -5
POINTS_CIVILIAN_WIN     =   8
POINTS_CIVILIAN_LOSE    =  -3
POINTS_DRAW             =  -1
POINTS_AFK_KICK         =  -4
POINTS_FALSE_ACCUSATION =  -2   # проголосовал за мирного, шпион победил

RATINGS_FILE = "ratings.json"


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


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
games = {}


# ─── ГЕНЕРАЦИЯ РОЛЕЙ ────────────────────────────────────────────────────────

def generate_roles(players, theme):
    chance = random.random()

    # 10% — режим вопросов (обычный шпион, но ход идёт через вопрос)
    if chance <= 0.10:
        spy_player = random.choice(players)
        word = random.choice(WORDS[theme])
        roles = {
            p['id']: ("ШПИОН", None) if p == spy_player else ("МИРНЫЙ", word)
            for p in players
        }
        spy_ids = [spy_player['id']]
        mode_text = "❓ Режим вопросов! Бот будет задавать вопросы каждому игроку."
        game_mode = "questions"

    # 5% — два шпиона
    elif 0.10 < chance <= 0.15 and len(players) >= 4:
        spy_players = random.sample(players, 2)
        word = random.choice(WORDS[theme])
        roles = {
            p['id']: ("ШПИОН", None) if p in spy_players else ("МИРНЫЙ", word)
            for p in players
        }
        spy_ids = [p['id'] for p in spy_players]
        mode_text = "⚠️ В этом раунде может быть больше одного шпиона..."
        game_mode = "double_spy"

    # 5% — нет шпиона
    elif 0.15 < chance <= 0.20:
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

    # 80% — обычная игра
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

    # В режиме вопросов — задаём случайный вопрос
    if game.get('game_mode') == 'questions':
        question = random.choice(QUESTIONS)
        await bot.send_message(
            chat_id,
            f"❓ Вопрос для <b>{player_name}</b>:\n<i>{question}</i>\n\nУ вас {THINK_TIME} секунд!",
            parse_mode="HTML"
        )
    else:
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
        if game.get('game_mode') != 'questions':
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


# ─── КОМАНДЫ ─────────────────────────────────────────────────────────────────

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
        "<b>Цель:</b>\n"
        "• <b>Мирные</b> — вычислить шпиона и проголосовать за него.\n"
        "• <b>Шпион</b> — остаться незамеченным и угадать слово.\n\n"
        "<b>Как играть:</b>\n"
        "1️⃣ /spy в группе → выбрать количество игроков\n"
        "2️⃣ Все нажимают ✋ Участвовать\n"
        "3️⃣ Создатель выбирает тему\n"
        "4️⃣ Каждый получает роль в ЛС\n"
        f"5️⃣ После {ROUNDS_BEFORE_VOTE} кругов — голосование\n\n"
        "<b>Особые режимы (случайные):</b>\n"
        "❓ <b>Режим вопросов (10%)</b> — бот задаёт вопрос каждому игроку\n"
        "⚠️ <b>Два шпиона (5%)</b> — сразу двое шпионов\n"
        "🧐 <b>Без шпиона (5%)</b> — у одного игрока другое слово\n\n"
        "<b>Очки:</b>\n"
        f"🏆 Шпион победил: +{POINTS_SPY_WIN}\n"
        f"☠️ Шпион пойман: {POINTS_SPY_LOSE}\n"
        f"🎉 Мирный победил: +{POINTS_CIVILIAN_WIN}\n"
        f"😔 Мирный проиграл: {POINTS_CIVILIAN_LOSE}\n"
        f"🤝 Ничья: {POINTS_DRAW}\n"
        f"🗳 Ложное обвинение: {POINTS_FALSE_ACCUSATION} (голосовал за мирного, шпион победил)\n"
        f"💤 AFK кик: {POINTS_AFK_KICK}\n\n"
        "<b>Команды:</b>\n"
        "/spy — начать игру\n"
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

    sorted_players = sorted(ratings[cid].values(), key=lambda x: x['points'], reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>Топ игроков группы:</b>\n"]
    for i, player in enumerate(sorted_players[:10]):
        medal = medals[i] if i < 3 else f"{i + 1}."
        lines.append(f"{medal} {player['name']} — <b>{player['points']}</b> очков")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ─── ЛОББИ ───────────────────────────────────────────────────────────────────

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
    start_text = (
        f"🎮 Игра началась!\n{mode_info}\n\n"
        f"Голосование появится после {ROUNDS_BEFORE_VOTE} кругов.\n\n"
    )
    if game_mode == 'questions':
        start_text += f"❓ Бот задаёт вопрос — <b>{first_player}</b> отвечает первым!"
    else:
        start_text += f"🗣 Первым высказывается: <b>{first_player}</b>"

    await callback.message.edit_text(start_text, parse_mode="HTML")
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
                result_lines.append("Один игрок получил другое слово из той же темы.")
                result_lines.append("Очки за этот раунд не начисляются.")

            else:  # normal или questions
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

    # ── Начисление очков ──
    if game_mode != "no_spy":
        points_lines = ["\n🏅 Очки за раунд:"]
        for player in game['players']:
            is_spy = player['id'] in spy_ids
            extra = ""

            if is_draw:
                pts = POINTS_DRAW
                label = f"{pts} (ничья 🤝)"
            elif is_spy:
                pts = POINTS_SPY_WIN if spy_won else POINTS_SPY_LOSE
                label = f"{'+' if pts > 0 else ''}{pts} (шпион {'победил 🏆' if spy_won else 'пойман ☠️'})"
            else:
                pts = POINTS_CIVILIAN_WIN if not spy_won else POINTS_CIVILIAN_LOSE
                label = f"{'+' if pts > 0 else ''}{pts} (мирный {'победил 🎉' if not spy_won else 'проиграл 😔'})"

                # Штраф за ложное обвинение: мирный проиграл И голосовал за другого мирного
                if spy_won and not is_spy and not is_draw:
                    voted_for = game['votes'].get(player['id'])
                    if voted_for is not None and voted_for not in spy_ids:
                        pts += POINTS_FALSE_ACCUSATION
                        extra = f" {POINTS_FALSE_ACCUSATION} (ложное обвинение 🗳)"

            add_points(ratings, chat_id, player['id'], player['name'], pts)
            points_lines.append(f"• {player['name']}: {'+' if pts > 0 else ''}{pts}{extra}")

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


# ─── ВЕБ-СЕРВЕР ──────────────────────────────────────────────────────────────

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
