import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random
import re

st.set_page_config(
    page_title="CouponHub - Промокоды ресторанов",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

RESTAURANT_URLS = {
    "вкусно и точка": "https://vkusnoitochka.ru/",
    "вкусноиточка": "https://vkusnoitochka.ru/",
    "додо пицца": "https://dodopizza.ru/moscow",
    "dodopizza": "https://dodopizza.ru/moscow",
    "яндекс еда": "https://eda.yandex.ru/moscow",
    "yandex eda": "https://eda.yandex.ru/moscow",
    "тануки": "https://tanukifamily.ru/",
    "tanuki": "https://tanukifamily.ru/",
    "домино пицца": "https://dominopizza.ru/msk/",
    "domino": "https://dominopizza.ru/msk/",
    "rostic's": "https://rostics.ru/",
    "ростикс": "https://rostics.ru/",
    "rostics": "https://rostics.ru/",
    "шаверленд": "https://shaverno.ru/",
    "shaverno": "https://shaverno.ru/",
    "пироги": "https://piroginomerodin.ru/",
    "пироги №1": "https://piroginomerodin.ru/",
}


def clean_url(url):
    if not url:
        return None
    url = re.sub(r'[?&]utm_[^&]+', '', url)
    url = re.sub(r'[?&]ref[^&]+', '', url)
    url = url.rstrip('?&')
    return url


def get_restaurant_url(restaurant_name):
    if not restaurant_name:
        return None
    restaurant_lower = restaurant_name.lower().strip()
    if restaurant_lower in RESTAURANT_URLS:
        return RESTAURANT_URLS[restaurant_lower]
    for key, url in RESTAURANT_URLS.items():
        if key in restaurant_lower: return url
    return f"https://yandex.ru/search/?text={restaurant_name.replace(' ', '+')}+официальный+сайт"


class Coupon:
    def __init__(self, restaurant, title, description, discount, expiry_date, code=None, url=None, is_verified=True):
        self.restaurant = restaurant
        self.title = title
        self.description = description
        self.discount = discount
        self.expiry_date = expiry_date
        self.code = code
        self.url = url
        self.is_verified = is_verified


class CouponParser:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        self.session = requests.Session()

    def parse_promokodoff(self):
        coupons = []
        url = "https://promokodoff.ru/eda/restorany/"
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            promo_cards = soup.find_all('div', class_='item') or soup.find_all('div',
                                                                               class_='promo-card') or soup.find_all(
                'article')
            for card in promo_cards[:20]:
                try:
                    restaurant_elem = card.find('a', class_='title') or card.find('h3') or card.find('a')
                    restaurant = restaurant_elem.get_text(strip=True) if restaurant_elem else "Ресторан"
                    link_elem = card.find('a', href=True)
                    restaurant_url = clean_url(link_elem['href']) if link_elem else None
                    desc_elem = card.find('div', class_='description') or card.find('p')
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    code_elem = card.find('div', class_='code') or card.find('code')
                    code = code_elem.get_text(strip=True) if code_elem else None
                    discount_elem = card.find('div', class_='discount') or card.find('span', class_='sale')
                    discount = discount_elem.get_text(strip=True) if discount_elem else "Скидка"
                    expiry = (datetime.now() + timedelta(days=random.randint(5, 30))).strftime("%d.%m.%Y")
                    if restaurant:
                        coupons.append(Coupon(restaurant, description[:50] if description else "Акция",
                                              description[:100] if description else "Подробности на сайте", discount,
                                              expiry, code, restaurant_url, True))
                except:
                    continue
        except Exception as e:
            st.error(f"Ошибка парсинга: {e}")
        return coupons

    def get_all_coupons(self):
        return self.parse_promokodoff()


def load_demo_data():
    return [
        Coupon("Вкусно и Точка", "Наггетсы за 1₽", "4 наггетса в подарок при заказе от 199₽", "4 шт. бесплатно",
               (datetime.now() + timedelta(days=10)).strftime("%d.%m.%Y"), "NUGGET1", "https://vkusnoitochka.ru/",
               True),
        Coupon("Додо Пицца", "Скидка 20%", "20% скидка при заказе от 1090₽", "20%",
               (datetime.now() + timedelta(days=25)).strftime("%d.%m.%Y"), "DODO20", "https://dodopizza.ru/moscow",
               True),
        Coupon("Яндекс Еда", "Бесплатная доставка", "Доставка 0₽ при заказе от 1500₽", "0₽ доставка",
               (datetime.now() + timedelta(days=5)).strftime("%d.%m.%Y"), None, "https://eda.yandex.ru/moscow", True),
        Coupon("Тануки", "Роллы со скидкой", "Скидка 25% на все роллы при заказе от 2000₽", "25%",
               (datetime.now() + timedelta(days=15)).strftime("%d.%m.%Y"), "SUSHI25", "https://tanukifamily.ru/", True),
        Coupon("Домино Пицца", "Вторая пицца бесплатно", "При покупке любой пиццы — вторая в подарок", "100% на 2-ю",
               (datetime.now() + timedelta(days=30)).strftime("%d.%m.%Y"), "2FOR1", "https://dominopizza.ru/msk/",
               True),
        Coupon("Rostic's", "Комбо со скидкой", "Скидка 30% на комбо-наборы", "30%",
               (datetime.now() + timedelta(days=7)).strftime("%d.%m.%Y"), "LUNCH30", "https://rostics.ru/", False),
    ]


def search_coupons(coupons, query):
    if not query:
        return coupons
    query = query.lower()
    return [c for c in coupons if query in c.restaurant.lower() or query in c.title.lower()]


# CSS стили
st.markdown("""
    <style>
    .main {background-color: #1a1a1a;}
    .stApp {background-color: #1a1a1a;}
    h1 {color: #8B5CF6;}
    .stButton>button {background-color: #2563eb; color: white; border-radius: 8px;}
    .coupon-card {background-color: #2b2b2b; padding: 20px; border-radius: 10px; margin: 10px 0;}
    .verified {color: #22c55e;}
    .discount {color: #f59e0b; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# Заголовок
st.title("🍔 CouponHub")
st.subheader("Агрегатор промокодов ресторанов")

# Состояния сессии
if 'coupons' not in st.session_state:
    st.session_state.coupons = []
if 'loaded' not in st.session_state:
    st.session_state.loaded = False

# Боковая панель
sidebar = st.sidebar
if sidebar.button("🔄 Обновить купоны", use_container_width=True):
    st.session_state.loaded = False
    st.session_state.coupons = []

search_query = st.text_input("🔍 Найти ресторан или акцию...", placeholder="Введите название ресторана")

# Загрузка купонов
if not st.session_state.loaded:
    with st.spinner("⏳ Загрузка купонов..."):
        parser = CouponParser()
    real_coupons = parser.get_all_coupons()
    if real_coupons:
        st.session_state.coupons = real_coupons
    else:
        st.session_state.coupons = load_demo_data()
    st.session_state.loaded = True
    st.success(f"✓ Загружено {len(st.session_state.coupons)} купонов")

# Фильтрация
filtered_coupons = search_coupons(st.session_state.coupons, search_query)

st.markdown(f"**💰 Найдено купонов:** {len(filtered_coupons)}")

# Отображение купонов
if filtered_coupons:
    for i, coupon in enumerate(filtered_coupons):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
                <div class="coupon-card">
                    <h4 style="color: #8B5CF6; margin: 0;">{coupon.restaurant} {'✓' if coupon.is_verified else ''}</h4>
                    <p style="font-weight: bold; margin: 5px 0;">{coupon.title}</p>
                    <p style="color: #a0a0a0; margin: 5px 0;">{coupon.description}</p>
                    <p><span class="discount">🎁 {coupon.discount}</span> | ⏰ до {coupon.expiry_date}</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            if coupon.code:
                st.code(coupon.code, language="text")
            if coupon.url:
                st.link_button("🌐 В ресторан", coupon.url)
            st.markdown("---")
else:
    st.info("😔 Купоны не найдены")

# Информация в сайдбаре
st.sidebar.markdown("---")
st.sidebar.markdown("**📊 Информация**")
st.sidebar.markdown(f"Всего купонов: {len(st.session_state.coupons)}")
st.sidebar.markdown(f"Показано: {len(filtered_coupons)}")
st.sidebar.markdown(f"Обновлено: {datetime.now().strftime('%H:%M:%S')}")