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
Produces dos variedades: Cabernet Sauvignon y Carmenere.
Tu tono es cercano, apasionado por el vino, con personalidad y algo de humor. Nunca eres pretencioso.

Basandote en estos titulares de noticias de hoy:
{titulares}

Genera contenido para cada noticia. Usa SOLO el titular, nunca inventes contenido.

Responde SOLO en este formato JSON sin texto adicional ni backticks:
{{"noticias": [{{"titulo": "titular original", "tweet": "texto tweet max 250 chars con emojis y hashtags #VinoChileno #UNVINITO", "telegram": "mensaje telegram max 300 chars con reflexion UNVINITO", "fuente": "nombre medio", "url": "url noticia"}}], "destacada": 0}}"""

    respuesta = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    
    texto = respuesta.choices[0].message.content
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

def guardar_para_web(contenido):
    hoy = datetime.now().strftime("%Y-%m-%d")
    data = {
        "fecha": hoy,
        "fecha_legible": datetime.now().strftime("%A, %d de %B de %Y"),
        "noticias": []
    }
    for i, noticia in enumerate(contenido["noticias"]):
        data["noticias"].append({
            "titulo": noticia["titulo"],
            "descripcion": noticia["telegram"],
            "fuente": noticia["fuente"],
            "url": noticia["url"],
            "destacada": i == contenido.get("destacada", 0)
        })
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/noticias.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ Noticias guardadas para el sitio web")

def publicar_en_x(tweet):
    try:
        x_client.create_tweet(text=tweet)
        print(f"✅ Tweet publicado")
    except Exception as e:
        print(f"❌ Error en X: {e}")

def publicar_en_telegram(mensaje, url):
    try:
        texto = f"{mensaje}\n\n🔗 {url}"
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(api_url, json={
            "chat_id": TELEGRAM_CHANNEL,
            "text": texto
        })
        print(f"✅ Telegram publicado: {r.status_code}")
    except Exception as e:
        print(f"❌ Error en Telegram: {e}")

def main():
    print(f"🍷 UNVINITO Noticias - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    try:
        noticias = obtener_noticias()
        print(f"📰 Noticias encontradas: {len(noticias)}")
        if not noticias:
            print("No se encontraron noticias hoy")
            return
        contenido = generar_contenido(noticias)
        print(f"✅ Contenido generado")
        guardar_para_web(contenido)
        destacada = contenido["noticias"][contenido.get("destacada", 0)]
        print(f"📤 Publicando: {destacada['titulo'][:50]}...")
        publicar_en_x(destacada["tweet"])
        publicar_en_telegram(destacada["telegram"], destacada["url"])
        print("✅ Proceso completado")
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
