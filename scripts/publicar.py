import os
import re
import feedparser
import tweepy
import requests
import json
import random
from datetime import datetime
import google.generativeai as genai

# Configurar Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")

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
SITIO_WEB = "https://clacontas.github.io/unvinito-noticias/"

# 40 categorías para ¿Lo sabías?
CATEGORIAS_LO_SABIAS = [
    "historia del vino chileno",
    "cómo se hace el vino",
    "curiosidades del mundo del vino",
    "estadísticas sorprendentes del vino",
    "mitos y verdades sobre el vino",
    "cómo catar un vino de forma simple",
    "cómo beberlo y servirlo mejor",
    "diferencias entre tipos de vino",
    "diferencias entre variedades de uva",
    "maridajes simples para el día a día",
    "qué comer con vino tinto chileno",
    "qué comer con Carménère",
    "qué comer con Cabernet Sauvignon",
    "maridajes inesperados que funcionan",
    "valles vitivinícolas de Chile",
    "el Valle de Colchagua y sus características",
    "por qué Chile produce vinos únicos",
    "exportaciones de vino chileno al mundo",
    "el vino en la cultura popular",
    "el vino en el cine y la música",
    "historia de variedades emblemáticas",
    "el Carménère y su historia en Chile",
    "el vino en momentos cotidianos",
    "el vino y las estaciones del año",
    "el vino y el clima de Chile",
    "tendencias del vino en el mundo",
    "vino natural y orgánico en Chile",
    "el vino sin alcohol y por qué existe",
    "el auge del enoturismo en Chile",
    "por qué el vino une a la gente",
    "el vino como regalo — qué considerar",
    "cómo hablar de vino sin saber mucho",
    "qué preguntar en una vinoteca",
    "por qué algunos vinos cuestan más",
    "cómo encontrar buenos vinos baratos",
    "qué significa relación precio-calidad en vino",
    "qué es un vino de autor y por qué importa",
    "la diferencia entre viña grande y pequeña",
    "por qué los vinos de autor son limitados",
    "el vino y la gastronomía chilena",
]

# Identidad por día
IDENTIDAD_DIA = {
    0: "Arrancar la semana sabiendo más",
    1: "La sorpresa corta del día",
    2: "A mitad de semana se antoja esto",
    3: "Dato para el fin de semana que se viene",
    4: "Y si abrimos un vinito esta noche...",
    5: "Sin plan, sin apuro, con copa en mano",
    6: "Toda gran historia comienza así",
}

NOMBRES_DIA = {
    0: "Lunes", 1: "Martes", 2: "Miércoles",
    3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"
}

CIERRES = [
    "Se antoja otro, ¿no? 🍷",
    "Así empiezan las mejores historias. 🍷",
    "Sin razón. Sin apuro. 🍷",
    "Toda gran historia comienza con un vinito. 🍷",
    "Se me antojó contártelo. 🍷",
    "Y si abrimos uno ahora. 🍷",
    "Hay más donde esto salió. 🍷",
]

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
    return noticias[:6]

def obtener_categoria_del_dia():
    dia_del_año = datetime.now().timetuple().tm_yday
    return CATEGORIAS_LO_SABIAS[dia_del_año % len(CATEGORIAS_LO_SABIAS)]

def obtener_cierre():
    dia_del_año = datetime.now().timetuple().tm_yday
    return CIERRES[dia_del_año % len(CIERRES)]

def generar_contenido(noticias):
    hoy = datetime.now()
    dia_semana = hoy.weekday()
    nombre_dia = NOMBRES_DIA[dia_semana]
    identidad = IDENTIDAD_DIA[dia_semana]
    categoria = obtener_categoria_del_dia()
    cierre = obtener_cierre()
    es_especial = dia_semana in [4, 6]  # Viernes o domingo
    titulares = "\n".join([f"{i+1}. {n['titulo']} ({n['fuente']})" 
                           for i, n in enumerate(noticias)])

    prompt = f"""Eres la voz de UNVINITO — vino chileno del Valle de Colchagua.

ESENCIA DE LA MARCA:
UNVINITO es espontáneo. No necesita ocasión especial.
Es el "se me antoja un vinito", el "y si abrimos un vinito", el "me tomaría un vinito".
Tagline: "Toda gran historia comienza con UNVINITO."

VOZ:
- Amigo con muy buen gusto que te manda un mensaje sin formalidad
- Cercano, espontáneo, con humor suave
- Nunca pretencioso, nunca técnico
- JAMÁS uses: maridaje formal, bouquet, notas organolépticas, sumiller
- SÍ puedes decir: "se antoja", "pide", "va perfecto con", "sin apuro"

HOY: {nombre_dia} {hoy.strftime('%d de %B de %Y')}
IDENTIDAD DEL DÍA: {identidad}

NOTICIAS DISPONIBLES:
{titulares}

CATEGORÍA ¿LO SABÍAS? HOY: {categoria}

REGLAS ABSOLUTAS:
- NUNCA inventes datos, fechas o cifras
- Solo usa información que puedas verificar
- Máximo 3 líneas por sección
- El tono debe sentirse como un WhatsApp de alguien con buen gusto

Genera SOLO este JSON sin backticks ni texto extra:
{{
  "noticia_titulo": "titular de la noticia más interesante para el consumidor de UNVINITO",
  "noticia_opinion": "2-3 líneas con opinión espontánea y cercana de UNVINITO sobre esta noticia",
  "noticia_fuente": "nombre del medio",
  "noticia_url_index": 0,
  "lo_sabias": "dato fascinante sobre '{categoria}' en 2-3 líneas, cercano, sin tecnicismos, que el lector repita en una conversación esta noche",
  "momento": "{'escena concreta para vivir con UNVINITO esta noche — música real o película real con contexto de por qué hoy, sin inventar datos' if es_especial else ''}",
  "tweet": "versión para X max 220 chars con personalidad UNVINITO, espontánea, con #VinoChileno #UNVINITO"
}}"""

    respuesta = model.generate_content(prompt)
    texto = respuesta.text.strip()
    print(f"Gemini: {texto[:300]}")
    texto = texto.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(texto)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', texto, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise

    idx = data.get("noticia_url_index", 0)
    data["noticia_url"] = noticias[idx]["link"] if idx < len(noticias) else noticias[0]["link"]
    data["cierre"] = cierre
    data["es_especial"] = es_especial
    data["nombre_dia"] = nombre_dia
    data["fecha"] = hoy.strftime("%d de %B")

    return data

def guardar_para_web(data):
    web_data = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "fecha_legible": f"{data['nombre_dia']} {data['fecha']}",
        "identidad": IDENTIDAD_DIA[datetime.now().weekday()],
        "noticias": [{
            "titulo": data["noticia_titulo"],
            "descripcion": data["noticia_opinion"],
            "fuente": data["noticia_fuente"],
            "url": data["noticia_url"],
            "destacada": True
        }],
        "lo_sabias": data["lo_sabias"],
        "momento": data.get("momento", ""),
        "cierre": data["cierre"]
    }
    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/noticias.json", "w", encoding="utf-8") as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    print("✅ Web actualizada")

def publicar_en_x(data):
    try:
        tweet = f"{data['tweet']}\n\n🔗 {SITIO_WEB}"
        x_client.create_tweet(text=tweet)
        print("✅ X publicado")
    except Exception as e:
        print(f"❌ Error X: {e}")

def publicar_en_telegram(data):
    try:
        msg = f"🍷 UNVINITO · {data['nombre_dia']} {data['fecha']}\n\n"
        msg += f"──────────────\n"
        msg += f"VINO\n"
        msg += f"──────────────\n"
        msg += f"{data['noticia_titulo']}\n\n"
        msg += f"{data['noticia_opinion']}\n"
        msg += f"📰 {data['noticia_fuente']}\n\n"
        msg += f"──────────────\n"
        msg += f"¿LO SABÍAS?\n"
        msg += f"──────────────\n"
        msg += f"{data['lo_sabias']}\n\n"

        if data.get("es_especial") and data.get("momento"):
            msg += f"──────────────\n"
            msg += f"EL MOMENTO\n"
            msg += f"──────────────\n"
            msg += f"{data['momento']}\n\n"

        msg += f"──────────────\n"
        msg += f"{data['cierre']}\n"
        msg += f"{SITIO_WEB}"

        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(api_url, json={
            "chat_id": TELEGRAM_CHANNEL,
            "text": msg
        })
        print(f"✅ Telegram publicado: {r.status_code}")
    except Exception as e:
        print(f"❌ Error Telegram: {e}")

def main():
    print(f"🍷 UNVINITO · {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    try:
        noticias = obtener_noticias()
        print(f"📰 {len(noticias)} noticias encontradas")
        if not noticias:
            print("Sin noticias hoy")
            return
        data = generar_contenido(noticias)
        print("✅ Contenido generado")
        guardar_para_web(data)
        publicar_en_x(data)
        publicar_en_telegram(data)
        print("✅ Proceso completado")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
