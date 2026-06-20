import os
import feedparser
import tweepy
import requests
import json
from groq import Groq
from datetime import datetime

# Credenciales
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# X / Twitter
x_client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_SECRET"]
)

# Telegram
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHANNEL = os.environ["TELEGRAM_CHANNEL"]

# RSS de noticias de vino
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=vino+Chile&hl=es-419&gl=CL",
    "https://news.google.com/rss/search?q=vino+Colchagua&hl=es-419&gl=CL",
    "https://news.google.com/rss/search?q=vino+chileno+exportacion&hl=es-419&gl=CL",
]

def obtener_noticias():
    noticias = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            noticias.append({
                "titulo": entry.title,
                "link": entry.link,
                "fuente": entry.get("source", {}).get("title", "")
            })
    return noticias[:5]

def generar_contenido(noticias):
    titulares = "\n".join([f"- {n['titulo']} ({n['fuente']}) | {n['link']}" for n in noticias])
    
    prompt = f"""Eres el community manager de UNVINITO, una marca de vino chileno de autor del Valle de Colchagua. 
Produces dos variedades: Cabernet Sauvignon y Carménère.
Tu tono es cercano, apasionado por el vino, con personalidad y algo de humor. Nunca eres pretencioso.

Basándote en estos titulares de noticias de hoy:
{titulares}

Genera contenido para cada noticia. Usa SOLO el titular, nunca inventes contenido.

Responde SOLO en este formato JSON sin texto adicional:
{{
  "noticias": [
    {{
      "titulo": "titular original de la noticia",
      "tweet": "texto del tweet máximo 250 caracteres con 1-2 emojis y hashtags #VinoChileno #UNVINITO",
      "telegram": "mensaje para telegram con reflexión de UNVINITO máximo 300 caracteres",
      "fuente": "nombre del medio",
      "url": "url de la noticia"
    }}
  ],
  "destacada": 0
}}"""

    respuesta = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
