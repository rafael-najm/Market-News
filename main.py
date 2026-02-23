import feedparser
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from dateutil import parser as dateparser
from datetime import timezone
import hashlib
import time
import re
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from datetime import timedelta
import json
import os


# ================= CONFIG =================

WEBHOOK_URL = "WEBHOOK_AQUI"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

translator = GoogleTranslator(source="auto", target="pt")
CACHE_FILE = "enviados.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            pass
    return set()

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(cache), f, ensure_ascii=False, indent=2)

CACHE = load_cache()


# ================= FONTES =================

FEEDS = {
    "TradingView": {
        "url": "https://www.tradingview.com/rss/",
        "traduzir": True,
        "tipo": "Mercado Global"
    },
    "ForexFactory": {
        "url": "https://nfs.faireconomy.media/ff_calendar_thisweek.xml",
        "traduzir": False,
        "tipo": "Evento Macro"
    },
    "InfoMoney": {
        "url": "https://www.infomoney.com.br/feed/",
        "traduzir": False,
        "tipo": "Mercado BR"
    },
    "Bom Dia Mercado": {
        "url": "https://www.bomdiamercado.com.br/feed/",
        "traduzir": False,
        "tipo": "Mercado BR"
    },
        # ================= INVESTING =================

    "Investing - Technical Overview": {
        "url": "https://br.investing.com/rss/market_overview_Technical.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Fundamental Overview": {
        "url": "https://br.investing.com/rss/market_overview_Fundamental.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Economia": {
        "url": "https://br.investing.com/rss/news_301.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Ações": {
        "url": "https://br.investing.com/rss/news_1065.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Índices": {
        "url": "https://br.investing.com/rss/news_1063.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Moedas": {
        "url": "https://br.investing.com/rss/news_1061.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Commodities": {
        "url": "https://br.investing.com/rss/news_462.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Cripto": {
        "url": "https://br.investing.com/rss/news_357.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - ETFs": {
        "url": "https://br.investing.com/rss/news_356.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Geral": {
        "url": "https://br.investing.com/rss/news_1.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Análises": {
        "url": "https://br.investing.com/rss/news_289.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Renda Fixa": {
        "url": "https://br.investing.com/rss/news_477.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Política Econômica": {
        "url": "https://br.investing.com/rss/news_11.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Brasil": {
        "url": "https://br.investing.com/rss/news_25.rss",
        "traduzir": False,
        "tipo": "Mercado BR"
    },
    "Investing - EUA": {
        "url": "https://br.investing.com/rss/news_95.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Europa": {
        "url": "https://br.investing.com/rss/news_12.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },
    "Investing - Ásia": {
        "url": "https://br.investing.com/rss/news_14.rss",
        "traduzir": False,
        "tipo": "Mercado Global"
    },

}

# ================= FILTROS =================

BLACKLIST = [
    "atp", "tênis", "futebol", "campeonato", "jogo", "partida",
    "show", "cantor", "atriz", "ator", "filme", "série",
    "bbb", "reality", "celebridade", "onde assistir",
    "estreia", "horário do jogo", "congresso", "senado", "fake"
]

HIGH_IMPACT = [
    "fed", "fomc", "juros", "interest rate",
    "cpi", "inflação", "pmi", "gdp", "pib",
    "payroll", "emprego",
    "guerra", "conflito", "ataque", "sanção",
    "petróleo", "gás", "energia",
    "china", "taiwan", "israel", "irã", "rússia",
    "crise", "default"
]

MEDIUM_IMPACT = [
    "ações", "bolsa", "stocks", "índice",
    "commodities", "dólar", "câmbio",
    "yield", "treasury", "futuros",
    "ibovespa", "b3", "selic"
]

# ================= TAGS & EMOJI =================

TAGS = {
    "FX": ["dólar", "câmbio", "fx", "yield", "treasury"],
    "RATES": ["juros", "fed", "fomc", "cpi", "inflação"],
    "EQUITIES": ["ações", "bolsa", "stocks", "índice", "ibovespa"],
    "COMMODITIES": ["petróleo", "gás", "ouro", "commodities"],
    "GEO": ["guerra", "conflito", "sanção", "israel", "china", "rússia"],
    "MACRO": ["pib", "gdp", "emprego", "payroll", "pmi"]
}

EMOJI = {
    "FX": "💱",
    "RATES": "📉",
    "EQUITIES": "📈",
    "COMMODITIES": "🛢️",
    "GEO": "🌍",
    "MACRO": "🧠"
}

# ================= UTIL =================

def hash_url(url):
    return hashlib.md5(url.encode()).hexdigest()

def proibido(texto):
    t = texto.lower()
    return any(b in t for b in BLACKLIST)

def impacto(texto):
    t = texto.lower()
    if any(k in t for k in HIGH_IMPACT):
        return "ALTO"
    if any(k in t for k in MEDIUM_IMPACT):
        return "MEDIO"
    return "BAIXO"

def detectar_tags(texto):
    t = texto.lower()
    tags = [tag for tag, kws in TAGS.items() if any(k in t for k in kws)]
    return tags or ["MACRO"]

def get_published(entry):
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            dt = datetime(*entry.published_parsed[:6])
            dt = dt - timedelta(hours=3)  # 🔥 volta 3 horas
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            pass

    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            dt = datetime(*entry.updated_parsed[:6])
            dt = dt - timedelta(hours=3)  # 🔥 volta 3 horas
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            pass

    return "Data não informada"

# ================= FORMATAÇÃO =================

def limpar_texto(texto):
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"(Leia mais|Saiba mais).*", "", texto, flags=re.I)
    return texto.strip()

def formatar_briefing(texto, limite=900):
    texto = limpar_texto(texto)

    frases = re.split(r'(?<=[.!?])\s+', texto)

    paragrafos = []
    atual = ""

    for f in frases:
        # monta parágrafos de até ~300 caracteres
        if len(atual) + len(f) <= 300:
            atual += f + " "
        else:
            paragrafos.append(atual.strip())
            atual = f + " "

    if atual:
        paragrafos.append(atual.strip())

    # agora monta o texto FINAL respeitando parágrafo
    final = ""
    for p in paragrafos:
        if len(final) + len(p) + 2 <= limite:
            final += p + "\n\n"
        else:
            break

    return final.strip()


# ================= SCRAPING =================

def fetch_article_text(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        paragraphs = soup.find_all("p")
        texto = " ".join(
            p.get_text(strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 60
        )

        return texto if texto else None
    except:
        return None

# ================= DISCORD =================

def send_discord(title, body, source, tipo, url, published):
    payload = {
        "embeds": [{
            "title": title[:256],
            "url": url,
            "description": body[:4000],
            "color":  65280,
            "footer": {
                "text": f"{source} • {tipo} • {published}"
            }
        }]
    }
    requests.post(WEBHOOK_URL, json=payload, timeout=10)

# ================= PROCESS =================

def process_feed(name, cfg):
    feed = feedparser.parse(cfg["url"])

    for entry in feed.entries[:6]:
        url = entry.get("link")
        if not url:
            continue

        uid = hash_url(url)
        if uid in CACHE:
            continue

        title = entry.get("title", "").strip()
        published = get_published(entry)

        article = fetch_article_text(url)
        if not article:
            article = entry.get("summary", title)

        if cfg["traduzir"]:
            try:
                title = translator.translate(title)
                article = translator.translate(article)
            except:
                pass

        texto_base = f"{title} {article}"

        if proibido(texto_base):
            continue

        level = impacto(texto_base)
        if level == "BAIXO":
            continue

        if cfg["tipo"] != "Mercado BR" and level != "ALTO":
            continue


        tags = detectar_tags(texto_base)
        emoji = EMOJI.get(tags[0], "🧠")
        tag_str = " • ".join(tags)

        titulo_final = f"{emoji} [{tag_str}] {title}"
        corpo = formatar_briefing(article)

        send_discord(
            title=titulo_final,
            body=corpo,
            source=name,
            tipo=cfg["tipo"],
            url=url,
            published=published
        )
        CACHE.add(uid)
        save_cache(CACHE)


# ================= LOOP =================

def run():
    print("🟢 Bot iniciado")
    while True:
        for name, cfg in FEEDS.items():
            process_feed(name, cfg)
        time.sleep(300)

if __name__ == "__main__":
    run()
