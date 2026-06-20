import os
import feedparser
import tweepy
import requests
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
    titulares = "\n".join([f"- {n['titulo']} ({n['fuente']})" for n in noticias])
    
    prompt = f"""Eres el community manager de UNVINITO, una marca de vino chileno de autor del Valle de Colchagua. 
Produces dos variedades: Cabernet Sauvignon y Carménère.
Tu tono es cercano, apasionado por el vino, con personalidad y algo de humor. Nunca eres pretencioso.

Basándote en estos titulares de noticias de hoy:
{titulares}

Genera:
1. Un TWEET de máximo 250 caracteres con la noticia más interesante. 
   Incluye 1-2 emojis relevantes y 2-3 hashtags como #VinoChileno #Colchagua #UNVINITO
   IMPORTANTE: Solo usa el titular, nunca inventes contenido del artículo.

2. Un MENSAJE para canal de Telegram más detallado (máximo 300 caracteres).
   Puedes agregar una reflexión breve desde la perspectiva de UNVINITO.

Responde SOLO en este formato JSON:
{{
  "tweet": "texto del tweet aquí",
  "telegram": "texto de telegram aquí",
  "fuente_url": "url de la noticia usada"
}}"""

    respuesta = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500
    )
    
    import json
    texto = respuesta.choices[0].message.content
    return json.loads(texto)

def publicar_en_x(tweet):
    try:
        x_client.create_tweet(text=tweet)
        print(f"✅ Tweet publicado: {tweet[:50]}...")
    except Exception as e:
        print(f"❌ Error en X: {e}")

def publicar_en_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={
            "chat_id": TELEGRAM_CHANNEL,
            "text": mensaje,
            "parse_mode": "HTML"
        })
        print(f"✅ Telegram publicado")
    except Exception as e:
        print(f"❌ Error en Telegram: {e}")

def main():
    print(f"🍷 UNVINITO Noticias - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    noticias = obtener_noticias()
    if not noticias:
        print("No se encontraron noticias hoy")
        return
    
    contenido = generar_contenido(noticias)
    
    publicar_en_x(contenido["tweet"])
    publicar_en_telegram(contenido["telegram"])
    
    print("✅ Proceso completado")

if __name__ == "__main__":
    main()
