import os
import re
import feedparser
import tweepy
import requests
import json
from datetime import datetime
from groq import Groq

# Configurar Groq
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
SITIO_WEB = "https://noticias.unvinito.cl"

# 40 categorías para ¿Lo sabías?
CATEGORIAS_LO_SABIAS = [
    "historia del vino chileno",
    "como se hace el vino",
    "curiosidades del mundo del vino",
    "estadisticas sorprendentes del vino",
    "mitos y verdades sobre el vino",
    "como catar un vino de forma simple",
    "como beberlo y servirlo mejor",
    "diferencias entre tipos de vino",
    "diferencias entre variedades de uva",
    "maridajes simples para el dia a dia",
    "que comer con vino tinto chileno",
    "que comer con Carmenere",
    "que comer con Cabernet Sauvignon",
    "maridajes inesperados que funcionan",
    "valles vitivinicolas de Chile",
    "el Valle de Colchagua y sus caracteristicas",
    "por que Chile produce vinos unicos",
    "exportaciones de vino chileno al mundo",
    "el vino en la cultura popular",
    "el vino en el cine y la musica",
    "historia de variedades emblematicas",
    "el Carmenere y su historia en Chile",
    "el vino en momentos cotidianos",
    "el vino y las estaciones del año",
    "el vino y el clima de Chile",
    "tendencias del vino en el mundo",
    "vino natural y organico en Chile",
    "el vino sin alcohol y por que existe",
    "el auge del enoturismo en Chile",
    "por que el vino une a la gente",
    "el vino como regalo que considerar",
    "como hablar de vino sin saber mucho",
    "que preguntar en una vinoteca",
    "por que algunos vinos cuestan mas",
    "como encontrar buenos vinos baratos",
    "que significa relacion precio calidad en vino",
    "que es un vino de autor y por que importa",
    "la diferencia entre vina grande y pequeña",
    "por que los vinos de autor son limitados",
    "el vino y la gastronomia chilena",
]

IDENTIDAD_DIA = {
    0: "Arrancar la semana sabiendo mas",
    1: "La sorpresa corta del dia",
    2: "A mitad de semana se antoja esto",
    3: "Dato para el fin de semana que se viene",
    4: "Y si abrimos un vinito esta noche...",
    5: "Sin plan, sin apuro, con copa en mano",
    6: "Toda gran historia comienza asi",
}

NOMBRES_DIA = {
    0: "Lunes", 1: "Martes", 2: "Miercoles",
    3: "Jueves", 4: "Viernes", 5: "Sabado", 6: "Domingo"
}

CIERRES = [
    "Se antoja otro, no? 🍷",
    "Asi empiezan las mejores historias. 🍷",
    "Sin razon. Sin apuro. 🍷",
    "Toda gran historia comienza con un vinito. 🍷",
    "Se me antojo contartelo. 🍷",
    "Y si abrimos uno ahora. 🍷",
    "Hay mas donde esto salio. 🍷",
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
    dia_del_anio = datetime.now().timetuple().tm_yday
    return CATEGORIAS_LO_SABIAS[dia_del_anio % len(CATEGORIAS_LO_SABIAS)]

def obtener_cierre():
    dia_del_anio = datetime.now().timetuple().tm_yday
    return CIERRES[dia_del_anio % len(CIERRES)]

def generar_contenido(noticias):
    hoy = datetime.now()
    dia_semana = hoy.weekday()
    nombre_dia = NOMBRES_DIA[dia_semana]
    identidad = IDENTIDAD_DIA[dia_semana]
    categoria = obtener_categoria_del_dia()
    cierre = obtener_cierre()
    es_especial = dia_semana in [4, 6]

    titulares = "\n".join([
        f"{i+1}. TITULAR: {n['titulo']} | FUENTE: {n['fuente']} | URL_INDEX: {i}"
        for i, n in enumerate(noticias)
    ])

    prompt = f"""Eres la voz de UNVINITO, vino chileno del Valle de Colchagua.

ESENCIA DE LA MARCA:
UNVINITO es espontaneo. No necesita ocasion especial.
Es el "se me antoja un vinito", el "y si abrimos un vinito", el "me tomaria un vinito".
Tagline: "Toda gran historia comienza con UNVINITO."

VOZ:
- Amigo con muy buen gusto que manda un mensaje sin formalidad
- Cercano, espontaneo, con humor suave
- JAMAS uses: maridaje formal, bouquet, notas organolepticas, sumiller
- SI puedes decir: "se antoja", "pide", "va perfecto con", "sin apuro"

HOY: {nombre_dia} {hoy.strftime('%d de %B de %Y')}
IDENTIDAD DEL DIA: {identidad}

NOTICIAS DISPONIBLES (elige la mas relevante para el consumidor de UNVINITO):
{titulares}

CATEGORIA LO SABIAS HOY: {categoria}

REGLAS ABSOLUTAS — VIOLACION GRAVE SI NO SE CUMPLEN:
1. El campo "noticia_titulo" debe ser COPIA EXACTA del titular original, sin cambiar ni una palabra
2. NUNCA reescribas, mejores ni inventes un titular propio
3. NUNCA inventes datos, fechas o cifras que no esten en las noticias
4. El campo "noticia_url_index" debe ser el numero exacto que aparece en URL_INDEX
5. Maximo 3 lineas por seccion
6. Tono como WhatsApp de alguien con buen gusto
7. En LO SABIAS evita datos obvios como "el vino tinto va con carnes". Busca el angulo inesperado que sorprenda
8. En EL MOMENTO usa el contexto real del dia para crear la escena — no algo generico que funcione cualquier dia

Responde SOLO con este JSON sin backticks ni texto extra:
{{"noticia_titulo": "COPIA EXACTA del titular original sin modificar", "noticia_opinion": "2-3 lineas opinion espontanea UNVINITO sobre esta noticia", "noticia_fuente": "nombre exacto del medio", "noticia_url_index": 0, "lo_sabias": "dato sobre {categoria} que el 90% de la gente NO sabe. Debe sorprender. Evita lo obvio. Termina con una consecuencia practica para el lector esta noche. 2-3 lineas maximo, sin tecnicismos, que el lector pueda repetir en una conversacion y quedar bien",
"momento": "{'escena concreta y especifica para vivir con UNVINITO esta noche. Usa el contexto real del dia ' + nombre_dia + ' ' + hoy.strftime('%d de %B') + '. Conecta un momento cultural real (musica, pelicula, lugar) con por que encaja exactamente hoy — no cualquier dia. Sin inventar datos. Con emocion real.' if es_especial else ''}", "tweet": "opinion espontanea UNVINITO sobre la noticia max 220 chars con #VinoChileno #UNVINITO sin incluir el titular exacto"}}"""

    respuesta = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )

    texto = respuesta.choices[0].message.content.strip()
    print(f"Groq: {texto[:300]}")
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
    hoy = datetime.now().strftime("%Y-%m-%d")
    web_data = {
        "fecha": hoy,
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
    # Guardar como contenido de hoy
    with open("docs/data/noticias.json", "w", encoding="utf-8") as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    # Guardar histórico por fecha
    with open(f"docs/data/{hoy}.json", "w", encoding="utf-8") as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Web actualizada y guardado histórico {hoy}")

def publicar_en_x(data):
    try:
        x_client.create_tweet(text=data['tweet'])
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
        msg += f"LO SABIAS?\n"
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
