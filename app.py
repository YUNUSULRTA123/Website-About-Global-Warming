from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_
from flask_whooshee import Whooshee
from dotenv import load_dotenv
from flask_migrate import Migrate
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import logging
import random
import os
import re

load_dotenv()

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  

app = Flask(__name__)

whooshee = Whooshee()
whooshee.init_app(app)

logging.basicConfig(level=logging.INFO)

app.config['SECRET_KEY'] = '64ed2a434a7b07d3ced2c8b1496b2b2a3a1776b03118f532adfd88cf83ff3e10'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///global_warming.db'
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    avatar = db.Column(db.String(255), default='default.png')  # путь к аватарке
    bio = db.Column(db.Text, default='')
    registered_on = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Модель заметок (дневника)
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='notes')

@whooshee.register_model('title', 'content')
class DiaryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)

class Meme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='messages')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    try:
        url = 'https://tass.ru/tag/izmenenie-klimata'
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'html.parser')
        news_blocks = soup.select('.news-item__title a')
        rand_num = random.randint(3, 6)
        news = [
            {
                'title': item.get_text(strip=True),
                'link': f"https://tass.ru{item['href']}"
            }
            for item in news_blocks[:rand_num]
        ]

        # Похожие ссылки
        related_links = [
    {
        "title": "Климатические катастрофы участились в 3 раза – Gazeta.ru",
        "link": "https://www.gazeta.ru/science/news/2025/06/17/26057204.shtml"
    },
    {
        "title": "ООН: апрель стал самым жарким месяцем – news.un.org",
        "link": "https://news.un.org/ru/story/2024/05/1452116"
    },
    {
        "title": "Изменение климата и пожары в Европе – Copernicus",
        "link": "https://www.gazeta.ru/science/news/2024/08/15/23690629.shtml"
    },
    {
        "title": "UNEP: ущерб от климата странам Кавказа – report.az",
        "link": "https://report.az/ru/cop29/unep-izmenenie-klimata-nanosit-znachitelnyj-usherb-shesti-stranam-kavkaza"
    },
    {
        "title": "Арктика тает быстрее, чем ожидалось – National Geographic Россия",
        "link": "https://nat-geo.ru/news/2025/07/01/arktika-taet-bystree-chem-ozhidalos"
    },
    {
        "title": "Глобальное потепление и его влияние на сельское хозяйство – РИА Новости",
        "link": "https://ria.ru/20250420/globalnoe-poteplenie-1789563457.html"
    },
    {
        "title": "Как изменения климата влияют на биоразнообразие – WWF Россия",
        "link": "https://wwf.ru/resources/news/kak-izmeneniya-klimata-vliyayut-na-bioraznoobrazie"
    },
    {
        "title": "Планы России по сокращению выбросов к 2030 году – ТАСС",
        "link": "https://tass.ru/ekonomika/17483932"
    },
    {
        "title": "Последствия таяния вечной мерзлоты – РИА Новости",
        "link": "https://ria.ru/20250310/vernaya-morozlota-1788795432.html"
    },
    {
        "title": "Городские зоны риска: как климат меняет города – Коммерсантъ",
        "link": "https://kommersant.ru/doc/5142459"
    },
    {
        "title": "Климат и здоровье: рост заболеваний из-за жары – Медвестник",
        "link": "https://medvestnik.ru/content/news/Klimat-i-zdorove-rost-zabolevanij-iz-za-zhary.html"
    },
    {
        "title": "Международные соглашения по климату: что изменилось в 2025 году – РБК",
        "link": "https://www.rbc.ru/economics/2025/01/15/63bbefad9a79474c0b9a13c7"
    },
    {
        "title": "Инновации в борьбе с изменением климата – Ведомости",
        "link": "https://www.vedomosti.ru/technology/articles/2025/04/12/985432-innovatsii-v-borbe-s-izmeneniem-klimata"
    },
    {
        "title": "Влияние климатических изменений на Черное море – EcoTimes",
        "link": "https://ecotimes.ru/novosti/2025/06/07/vliyanie-klimaticheskih-izmenenij-na-chernoe-more"
    },
    {
        "title": "Возобновляемая энергия в России: перспективы и вызовы – Российская газета",
        "link": "https://rg.ru/2025/03/23/vozobnovljaemaja-energiia-perspektivy.html"
    },
    {
        "title": "Пожары в Сибири: причины и последствия – ТАСС",
        "link": "https://tass.ru/proisshestviya/17925643"
    },
    {
        "title": "Климат и экономика: как потепление влияет на рынки – Forbes Россия",
        "link": "https://www.forbes.ru/forbesrussia/491262-klimat-i-ekonomika-kak-poteplenie-vliyaet-na-rynki"
    },
    {
        "title": "Новые технологии улавливания углерода – Наука и жизнь",
        "link": "https://www.nkj.ru/news/57540/"
    },
    {
        "title": "Пластик и климат: как загрязнение влияет на глобальное потепление – Greenpeace Россия",
        "link": "https://greenpeace.org/ru/plastik-i-klimat/"
    },
    {
        "title": "Климатические миграции: где люди вынуждены покидать дома – Радио Свобода",
        "link": "https://www.svoboda.org/a/30952461.html"
    },
    {
        "title": "Лесные пожары и изменение климата: связь и последствия – Экологический Вестник",
        "link": "https://eco-vestnik.ru/lesnye-pozhary-i-izmenenie-klimata"
    },
    {
        "title": "Глобальная политика по борьбе с изменением климата: итоги и перспективы – Институт мировой экономики и международных отношений",
        "link": "https://imemo.ru/ru/publ/klimaticheskaya-politika-2025"
    },
    {
        "title": "Эффекты повышения уровня моря для прибрежных регионов России – МГУ Новости",
        "link": "https://msu.ru/news/2025/06/22/uvelichenie-urovnya-morya"
    },
    {
        "title": "Как малые города адаптируются к изменению климата – Российская газета",
        "link": "https://rg.ru/2025/05/11/malye-goroda-i-klimaticheskie-izmeneniya.html"
    },
    {
        "title": "Биоразнообразие и климат: что будет с редкими видами – WWF Россия",
        "link": "https://wwf.ru/resources/news/bioraznoobrazie-i-klimat"
    },
    {
        "title": "Роль океанов в регулировании климата – Научный журнал Nature",
        "link": "https://nature.com/articles/oceans-climate-regulation-2025"
    },
    {
        "title": "Как городские леса помогают бороться с изменением климата – Экология Сегодня",
        "link": "https://ecologytoday.ru/urban-forests-climate-2025"
    },
    {
        "title": "Климат и энергетика: переход на зеленую энергетику в России – Энергетический журнал",
        "link": "https://energyjournal.ru/2025/04/green-energy-russia"
    },
    {
        "title": "Оценка рисков для аграрного сектора из-за климатических изменений – Агробизнес сегодня",
        "link": "https://agrobiz.ru/climate-risks-2025"
    },
    {
        "title": "Воздействие засухи на водные ресурсы – Водный мир",
        "link": "https://waterworld.ru/2025/06/drought-impact"
    },
    {
        "title": "Экономические убытки от экстремальных погодных явлений в России – РБК",
        "link": "https://rbc.ru/economics/2025/07/01/extreme-weather-losses"
    },
    {
        "title": "COP28 в Дубае: ключевые решения и итоги – РИА Новости",
        "link": "https://ria.ru/20251115/cop28-itogi-1857293472.html"
    },
    {
        "title": "Подготовка к COP28: основные вызовы – ТАСС",
        "link": "https://tass.ru/obschestvo/18545678"
    },
    {
        "title": "Что ждать от COP28? Аналитика и прогнозы – РБК",
        "link": "https://www.rbc.ru/ekonomika/2025/10/01/cop28-analitika"
    },
    {
        "title": "COP29: обзор предварительных тем и задач – Ведомости",
        "link": "https://www.vedomosti.ru/environment/articles/2025/07/20/cop29-obzor"
    },
    {
        "title": "Как Россия готовится к COP29 – Интерфакс",
        "link": "https://interfax.ru/russia/794853"
    },
    {
        "title": "Влияние решений COP28 на энергетику стран СНГ – Энергетика сегодня",
        "link": "https://energytoday.ru/news/cop28-vliyanie-na-sng"
    },
    {
        "title": "Главные климатические цели COP28 – ООН Россия",
        "link": "https://news.un.org/ru/story/2025/11/1502999"
    },
    {
        "title": "COP28: изменение правил торговли углеродными квотами – Коммерсантъ",
        "link": "https://kommersant.ru/doc/5512345"
    },
    {
        "title": "Отчет по COP29: новые обязательства и финансирование – Всемирный банк",
        "link": "https://worldbank.org/cop29-report-2026"
    },
    {
        "title": "Эксперты о последствиях COP28 для глобального климата – ЭкоМир",
        "link": "https://ecomir.ru/analitika/cop28-posledstviya"
    },
    {
        "title": "COP29 и климатическое правосудие: что нового? – Human Rights Watch",
        "link": "https://hrw.org/ru/news/2026/cop29-klimaticheskoe-pravosudie"
    },
    {
        "title": "Роль молодёжи на COP28 – Молодежный форум ООН",
        "link": "https://youth.un.org/ru/story/cop28-youth"
    },
    {
        "title": "COP28 и технологии: инновационные решения для климата – Наука и жизнь",
        "link": "https://nkj.ru/articles/cop28-innovatsii-2025"
    },
    {
        "title": "Критика и ожидания от COP29 – ЭкоПортал",
        "link": "https://ecoportal.ru/news/2026/cop29-kritika"
    },
    {
        "title": "COP28: как меняются подходы к адаптации к климату – WWF Россия",
        "link": "https://wwf.ru/resources/news/cop28-adaptaciya"
    }
]



        return render_template('index.html', news=news, related_links=related_links)

    except Exception as e:
        return f'Ошибка загрузки новостей: {e}', 500

def clean_query(query):
    return re.sub(r'[^\w\s]', '', query.lower()).strip()


@app.route('/search')
def search():
    search_query = request.args.get('q', '').strip()
    results = []

    if not search_query:
        return render_template('search_results.html', results=[], query='')

    # Поиск по дневнику
    diary_results = DiaryEntry.query.filter(
        or_(
            DiaryEntry.title.ilike(f'%{search_query}%'),
            DiaryEntry.content.ilike(f'%{search_query}%')
        )
    ).all()

    # Поиск по мемам
    meme_results = Meme.query.filter(
        or_(
            Meme.description.ilike(f'%{search_query}%'),
            Meme.filename.ilike(f'%{search_query}%')
        )
    ).all()

    # Формируем общий список результатов
    for entry in diary_results:
        results.append({
            'type': 'diary',
            'title': entry.title,
            'content': entry.content
        })
    for meme in meme_results:
        results.append({
            'type': 'meme',
            'filename': meme.filename,
            'description': meme.description
        })

    return render_template('search_results.html', results=results, query=search_query)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password or len(username) < 3 or len(password) < 6:
            flash('Имя пользователя и пароль должны быть не короче 3 и 6 символов соответственно.')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует.')
            return redirect(url_for('register'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Регистрация прошла успешно. Войдите в систему.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('diary'))
        flash('Неверное имя пользователя или пароль.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        bio = request.form.get('bio')
        avatar_file = request.files.get('avatar')

        if bio:
            current_user.bio = bio

        if avatar_file and allowed_file(avatar_file.filename):
            filename = secure_filename(avatar_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            i = 1
            base, ext = os.path.splitext(filename)
            while os.path.exists(filepath):
                filename = f"{base}_{i}{ext}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                i += 1

            avatar_file.save(filepath)
            current_user.avatar = filename

        db.session.commit()
        flash('Профиль обновлён')
        return redirect(url_for('profile'))

    return render_template('edit_profile.html', user=current_user)


@app.route('/diary', methods=['GET', 'POST'])
@login_required
def diary():
    if request.method == 'POST':
        content = request.form['content']
        if content:
            note = Note(content=content, user=current_user)
            db.session.add(note)
            db.session.commit()
            flash('Заметка добавлена.')
        else:
            flash('Нельзя добавить пустую заметку.')
        return redirect(url_for('diary')) 
    notes = Note.query.filter_by(user_id=current_user.id).all()
    return render_template('diary.html', notes=notes)

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            msg = ChatMessage(content=content, user=current_user)
            db.session.add(msg)
            db.session.commit()
            return redirect(url_for('chat'))

    messages = ChatMessage.query.order_by(ChatMessage.timestamp.desc()).limit(50).all()[::-1]
    return render_template('chat.html', messages=messages)


# Раздел мемов (статичные примеры)
memes = [
    {'filename': 'mem1.png', 'description': 'Экологический мем 1'},
    {'filename': 'mem2.png', 'description': 'Экологический мем 2'},
]

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/memes', methods=['GET', 'POST'])
def memes_page():

    page = request.args.get('page', 1, type=int)
    per_page = 10
    memes_paginated = Meme.query.paginate(page=page, per_page=per_page, error_out=False)
    
    if request.method == 'POST':
        file = request.files.get('file')
        description = request.form.get('description')

        if not file or file.filename == '':
            flash('Файл не выбран')
            return redirect(url_for('memes_page'))

        if not description:
            flash('Описание не может быть пустым')
            return redirect(url_for('memes_page'))

        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                i = 1
                base, ext = os.path.splitext(filename)
                while os.path.exists(filepath):
                    filename = f"{base}_{i}{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    i += 1

                file.save(filepath)
                meme = Meme(filename=filename, description=description)
                db.session.add(meme)
                db.session.commit()
                flash('Мем добавлен успешно!')
            except Exception as e:
                flash(f'Ошибка загрузки файла: {e}')
            return redirect(url_for('memes_page'))
        else:
            flash('Недопустимый формат файла')
            return redirect(url_for('memes_page'))

    memes = Meme.query.all()
    return render_template('memes.html', memes=memes_paginated.items, pagination=memes_paginated)

@app.route('/memes/delete/<filename>', methods=['POST'])
@login_required
def delete_meme(filename):
    meme_to_delete = Meme.query.filter_by(filename=filename).first()
    if meme_to_delete:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(meme_to_delete)
        db.session.commit()
        flash(f'Мем {filename} удалён')
    else:
        flash('Мем не найден')
    return redirect(url_for('memes_page'))
# Пример простого бота-ассистента с базовыми ответами
@app.route('/bot', methods=['GET', 'POST'])
def bot():
    answer = None
    if request.method == 'POST':
        question = request.form['question'].lower()
        faq = {
            'озеленение городов': 'Озеленение городов помогает снижать температуру, очищать воздух и улучшать качество жизни.',
            'загрязнение воздуха': 'Загрязнение воздуха происходит из-за выбросов транспорта, промышленности и сжигания отходов.',
            'загрязнение воды': 'Загрязнение воды связано с промышленными сбросами, пластиком и химикатами, попадающими в реки и океаны.',
            'перепроизводство': 'Перепроизводство приводит к избыточному потреблению ресурсов и образованию ненужных отходов.',
            'быстрая мода': 'Быстрая мода — это производство дешёвой и краткосрочной одежды, наносящее вред окружающей среде.',
            'световое загрязнение': 'Световое загрязнение — избыточный искусственный свет, мешающий экосистемам и человеку.',
            'шумовое загрязнение': 'Шумовое загрязнение влияет на здоровье людей и животных, особенно в городах.',
            'углеродная нейтральность': 'Углеродная нейтральность — состояние, при котором все выбросы компенсируются мерами по их поглощению.',
            'электромобили': 'Электромобили работают на электричестве, не производят выхлопных газов и снижают загрязнение воздуха.',
            'гибридные автомобили': 'Гибридные авто сочетают бензиновый и электрический двигатель для повышения эффективности и снижения выбросов.',
            'водородная энергия': 'Водород может использоваться как чистое топливо, выделяющее только водяной пар при сгорании.',
            'зеленое строительство': 'Зелёное строительство включает энергоэффективные здания и использование экологичных материалов.',
            'экотуризм': 'Экотуризм — это путешествия с минимальным воздействием на природу и уважением к культуре местных жителей.',
            'энергетическая эффективность': 'Энергетическая эффективность — получение того же результата с меньшими затратами энергии.',
            'сельское хозяйство и климат': 'Сельское хозяйство влияет на климат через выбросы метана, удобрения и изменение земель.',
            'органическое земледелие': 'Органическое земледелие исключает синтетические удобрения и поддерживает здоровье почв и экосистем.',
            'агролесоводство': 'Агролесоводство — сочетание земледелия и посадки деревьев для устойчивого использования земли.',
            'восстановление экосистем': 'Восстановление экосистем — это меры по возвращению природе её первоначального состояния.',
            'глобальное потепление и здоровье': 'Изменение климата повышает риск заболеваний, тепловых волн и нехватки чистой воды.',
            'ледники': 'Ледники тают из-за повышения температуры, что повышает уровень мирового океана.',
            'заболачивание': 'Заболачивание может быть последствием повышения уровня воды или нарушения дренажа почвы.',
            'деградация почв': 'Деградация почв ухудшает их плодородие из-за вырубки, химии и эрозии.',
            'засуха': 'Засуха — длительный период без осадков, усиливающий нехватку воды и бедствия в сельском хозяйстве.',
            'наводнения': 'Наводнения — результат сильных дождей или подъёма уровня воды, часто усиливаются из-за изменения климата.',
            'лесные пожары': 'Пожары в лесах участились из-за жары и засух, они уничтожают экосистемы и ухудшают качество воздуха.',
            'глобальное потепление и океан': 'Потепление вызывает повышение температуры океана, гибель кораллов и миграции морских видов.',
            'коралловые рифы': 'Кораллы страдают от потепления воды и загрязнений, что угрожает морскому биоразнообразию.',
            'переносимые болезнями комары': 'Изменение климата расширяет ареал комаров, переносящих малярию и лихорадку денге.',
            'углеродный бюджет': 'Углеродный бюджет — это максимальное количество CO₂, которое можно выбросить, чтобы не превысить порог потепления.',
            'циркулярная экономика': 'Циркулярная экономика стремится к повторному использованию и переработке вместо производства отходов.',
            'переход на зелёную энергетику': 'Переход на зелёную энергетику включает отказ от ископаемого топлива в пользу возобновляемых источников.',
            'погодные аномалии': 'Погодные аномалии — необычные погодные явления, такие как сильная жара или ливни, связанные с изменением климата.',
            'озеленение крыш': 'Зелёные крыши снижают перегрев городов, очищают воздух и сохраняют влагу.',
            'урожай и климат': 'Сбои в климате могут нарушать сроки посева и снижать урожайность.',
            'экослед пищи': 'Продукты питания имеют разный экологический след, в том числе по выбросам, воде и земле.',
            'местные продукты': 'Покупка местных продуктов снижает транспортные выбросы и поддерживает местную экономику.',
            'вегетарианство и климат': 'Уменьшение потребления мяса снижает выбросы парниковых газов и давление на ресурсы.',
            'разделение мусора': 'Разделение мусора помогает эффективной переработке и снижает количество отходов.',
            'день Земли': 'День Земли отмечается 22 апреля и посвящён защите природы и климата.',
            'зелёный патруль': 'Зелёный патруль — добровольное участие граждан в наблюдении и защите окружающей среды.',
            'глобальные климатические соглашения': 'Климатические соглашения, такие как Парижское, направлены на снижение глобального потепления.',
            'IPCC': 'IPCC — международная организация, публикующая научные оценки о состоянии климата и прогнозах.',
            'вторичная переработка': 'Вторичная переработка — превращение использованных материалов во вторичное сырьё для новых товаров.',
            'транспорт и климат': 'Автотранспорт — один из главных источников выбросов CO₂, особенно в городах.',
            'разработка экологической политики': 'Экологическая политика — это меры государств по регулированию воздействия на природу и климат.',
            'компенсация выбросов': 'Компенсация выбросов включает посадку деревьев или финансирование зелёных проектов в обмен на загрязнение.',
            'талая вода': 'Талая вода от тающих льдов может изменить морские течения и повлиять на климат регионов.',
            'энергия солнца': 'Солнечная энергия — чистый источник, преобразуемый в электричество с помощью панелей.',
            'ветровая энергия': 'Энергия ветра вырабатывается с помощью турбин и не производит вредных выбросов.',
            'геотермальная энергия': 'Геотермальная энергия использует тепло недр Земли для отопления и генерации электричества.',
            'биомасса': 'Биомасса — это органические материалы, используемые для производства энергии, например, древесина или сельхозотходы.',
            'водная энергия': 'Гидроэнергия вырабатывается с помощью плотин и турбин на реках, но может нарушать экосистемы.',
        }

        found_answers = []
        for key, response in faq.items():
            key_words = key.lower().split()
            if all(word in question for word in key_words):
                found_answers.append(response)

        if found_answers:
            answer = ' '.join(found_answers)
        else:
            answer = 'Извините, я пока не знаю ответа на этот вопрос. Попробуйте задать вопрос другими словами.'

    return render_template('bot.html', answer=answer)

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Ошибка: {e}")
    return "Внутренняя ошибка сервера", 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаём таблицы в базе
    app.run(debug=True)
