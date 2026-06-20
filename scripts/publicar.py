import os
import re
import feedparser
import tweepy
import requests
import json
from groq import Groq
from datetime import datetime

# Credenciales
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

x_client = tweepy.Client(
    consumer_key=os.environ["X_API_KEY"],
    consumer_secret=os.environ["X_API_SECRET"],
    access_token=os.environ["X_ACCESS_TOKEN"],
    access_token_secret=os.environ["X_ACCESS_SECRET"]
)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHANNEL = os.environ["TELEGRAM_CHANNEL"]

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=vino+Chile&hl=es-419&gl=CL",
    "https://news.google.com/rss/search?q=vino+Colchagua&hl=es-419&gl=CL",
    "https://news.google.com/rss/search?q=vino+chileno+exportacion&hl=es-419&gl=CL",
]

SITIO_WEB = "https://clacontas.github.io/unvinito-noticias/"

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
    return noticias[:6]

def generar_contenido(noticias):
    titulares = "\n".join([f"{i+1}. {n['titulo']} ({n['fuente']})" 
                           for i, n in enumerate(noticias)])

    prompt = f"""Eres el community manager de UNVINITO, marca de vino chileno del Valle de Colchagua.
Produces Cabernet Sauvignon y Carmenere.
Tono cercano, apasionado, con humor. Nunca pretencioso.

Noticias disponibles hoy:
{titulares}

Genera contenido diferenciado para cada canal. Usa SOLO los titulares, nunca inventes.

Responde UNICAMENTE con este JSON sin backticks ni texto extra:
{{
  "noticias": [
    {{
      "titulo": "titular exacto noticia 1",
      "reflexion": "reflexion corta max 80 chars con voz UNVINITO",
      "fuente": "nombre del medio",
      "url_index": 0
    }},
    {{
      "titulo": "titular exacto noticia 2", 
      "reflexion": "reflexion corta max 80 chars con voz UNVINITO",
      "fuente": "nombre del medio",
      "url_index": 1
    }},
    {{
      "titulo": "titular exacto noticia 3",
      "reflexion": "reflexion corta max 80 chars con voz UNVINITO", 
      "fuente": "nombre del medio",
      "url_index": 2
    }}
  ],
  "tweet": "tweet max 220 chars sobre la noticia mas impactante con emojis #VinoChileno #UNVINITO"
}}"""

    respuesta = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )

    texto = respuesta.choices[0].message.content.strip()
    print(f"Respuesta Groq: {texto[:300]}")
    texto = texto.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(texto)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise

    # Agregar URLs reales
    for noticia in data["noticias"]:
        idx = noticia.get("url_index", 0)
        if idx < len(noticias):
            noticia["url"] = noticias[idx]["link"]
        else:
            noticia["url"] = noticias[0]["link"]

    return data

def guardar_para_web(data):
    hoy = datetime.now().strftime("%Y-%m-%d")
    web_data = {
        "fecha": hoy,
        "fecha_legible": datetime.now().strftime("%A, %d de %B de %Y"),
        "noticias": []
    }
    for i, n in enumerate(data["noticias"]):
        web_data["noticias"].append({
            "titulo": n["titulo"],
            "descripcion": n["reflexion"],
            "fuente": n["fuente"],
            "url": n["url"],
            "destacada": i == 0
        })
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/noticias.json", "w", encoding="utf-8") as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    print("✅ Sitio web actualizado")

def publicar_en_x(tweet):
    try:
        x_client.create_tweet(text=f"{tweet}\n\n🔗 {SITIO_WEB}")
        print("✅ Tweet publicado")
    except Exception as e:
        print(f"❌ Error en X: {e}")

def publicar_en_telegram(data):
    try:
        hoy = datetime.now().strftime("%d %B %Y")
        mensaje = f"🍷 UNVINITO Noticias · {hoy}\n\n"
        
        for i, n in enumerate(data["noticias"], 1):
            emoji = ["1️⃣", "2️⃣", "3️⃣"][i-1]
            mensaje += f"{emoji} {n['titulo']}\n"
            mensaje += f"💬 {n['reflexion']}\n"
            mensaje += f"📰 {n['fuente']}\n\n"
        
        mensaje += f"🔗 {SITIO_WEB}"

        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(api_url, json={
            "chat_id": TELEGRAM_CHANNEL,
            "text": mensaje
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

        data = generar_contenido(noticias)
        print(f"✅ Contenido generado para {len(data['noticias'])} noticias")

        guardar_para_web(data)
        publicar_en_x(data["tweet"])
        publicar_en_telegram(data)

        print("✅ Proceso completado")
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
