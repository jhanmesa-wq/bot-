import json
import httpx
import datetime
import os
import base64
import io
from io import BytesIO
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from flask import Flask
from threading import Thread
import asyncio
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

BTN_VOLVER = InlineKeyboardMarkup([
    [InlineKeyboardButton("🏠 Volver al inicio", callback_data="menu_inicio")]
])


# Forzar la creación de un event loop si no existe en este hilo
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

app_flask = Flask('')

@app_flask.route('/')
def home():
    return "Bot activo"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = [str(os.getenv("ADMIN_ID"))] # Lista para poder agregar varios admins
ARCHIVO_USUARIOS = os.getenv("ARCHIVO_USUARIOS") or "usuarios.json"
BOT_USER = "@SpecterDox44_bot"
BOT_NAME = "⚜ DATA_PERU⚜"
BASE_URL = "https://api-codart.cgrt.org"

PRECIOS = {
    "dni": 4, "agv": 8, "telpcel": 15, "facial": 30, "ruc": 5, "suel": 5,
    "denuncia": 10, "placa": 12, "nm": 6, "hsoat": 8, "denpla": 30, "dnit": 5, "telp": 15
}

# ===== FUNCIONES BASE =====
def cargar_usuarios():
    try:
        with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def guardar_usuarios(data):
    with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_fecha():
    return datetime.datetime.now().strftime("%d/%m/%Y - %I:%M:%S %p")

async def validar_creditos(user_id, comando, usuarios):
    costo = PRECIOS[comando]
    if usuarios.get(user_id, {}).get("creditos", 0) < costo:
        return False, f"No tienes creditos suficientes. Necesitas {costo}. Usa /buy"
    return True, costo

async def consultar_api_get(url):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=headers)
            return r.json()
    except Exception as e:
        return {"error": str(e)}

# ===== COMANDOS GENERALES =====
async def den(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Uso correcto:\n<code>/den 12345678</code>",
            parse_mode="HTML"
        )
        return

    dni = context.args[0]

    if not (dni.isdigit() and len(dni) == 8):
        await update.message.reply_text("❌ El DNI debe contener 8 dígitos.")
        return

    url = f"https://api-codart.cgrt.org/api/v1/consultas/fd/den/{dni}"

    try:
        data = await consultar_api_get(url)

        if not data.get("success"):
            await update.message.reply_text("❌ No se encontraron denuncias.")
            return

        info = data["data"]

        mensaje = (
            "🚨 <b>CONSULTA DE DENUNCIAS</b>\n\n"
            f"🆔 <b>DNI:</b> <code>{info['consulta']}</code>\n"
            f"📄 <b>Total:</b> {info['cantidad_denuncias']}\n\n"
        )

        for d in info["denuncias"]:
            mensaje += (
                f"<b>📌 Denuncia #{d['numero']}</b>\n"
                f"👤 <b>Tipo:</b> {d['tipo']}\n"
                f"📑 <b>N° Orden:</b> {d['n_orden']}\n"
                f"📅 <b>Fecha Hecho:</b> {d['f_hecho']}\n"
                f"🗂 <b>Registro:</b> {d['f_registro']}\n"
                f"📋 <b>Condición:</b> {d['condicion']}\n"
                f"📝 <b>Resumen:</b> {d['resumen']}\n"
                "━━━━━━━━━━━━━━\n"
            )

        await update.message.reply_text(
            mensaje,
            parse_mode="HTML"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Error:\n<code>{e}</code>", parse_mode="HTML")
        await update.message.reply_text(
    texto,
    parse_mode="HTML",
    reply_markup=BTN_VOLVER
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = f"""⚜️ <b>¡BIENVENIDO A DATA PERÚ!</b> ⚜️

━━━━━━━━━━━━━━━━━━

📌 <b>INFORMACIÓN DEL BOT</b>

🏷️ <b>Nombre:</b> {BOT_NAME}
👤 <b>Usuario:</b> {BOT_USER}
🚀 <b>Versión:</b> v2.1 CODART V1

━━━━━━━━━━━━━━━━━━

📚 <b>COMANDOS GENERALES</b>

📝 /register ➾ Registrar cuenta
📖 /cmds ➾ Lista de comandos
👤 /me ➾ Ver tu perfil
🛡️ /staff ➾ Ver el staff
💳 /buy ➾ Comprar créditos/días

━━━━━━━━━━━━━━━━━━

⚡ <b>EN CONSTANTE EVOLUCIÓN</b>

Gracias por utilizar <b>DATA PERÚ</b>.
"""

    await update.message.reply_text(
        texto,
        parse_mode="HTML"
    )
async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = InlineKeyboardMarkup([
        [
    InlineKeyboardButton("╔═ 🪪 RENIEC ═╗", callback_data="cmd_reniec"),
    InlineKeyboardButton("╔═ 🏢 RUC ═╗", callback_data="cmd_ruc")
],
[
    InlineKeyboardButton("╔═ 🚘 VEHÍCULOS ═╗", callback_data="cmd_vehiculos"),
    InlineKeyboardButton("╔═ 📱 TELÉFONO ═╗", callback_data="cmd_telefono")
],
[
    InlineKeyboardButton("╔═ ⚖️ DENUNCIAS ═╗", callback_data="cmd_denuncia"),
    InlineKeyboardButton("╔═ 💰 SUELDO ═╗", callback_data="cmd_sueldo")
],
[
    InlineKeyboardButton("╔═ 🧬 FACIAL ═╗", callback_data="cmd_facial"),
    InlineKeyboardButton("╔═ 💎 COMPRAR ═╗", callback_data="cmd_buy")
]
    ])

    texto = f"""╔══════════════════════════════╗
        ⚜️ 𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦 𝗣𝗘𝗥𝗨 ⚜️
╚══════════════════════════════╝

🚀 𝗟𝗔 𝗣𝗟𝗔𝗧𝗔𝗙𝗢𝗥𝗠𝗔 #𝟭 𝗗𝗘 𝗖𝗢𝗡𝗦𝗨𝗟𝗧𝗔𝗦

━━━━━━━━━━━━━━━━━━━━━━━

🛰️ 𝗔𝗖𝗖𝗘𝗗𝗘 𝗔 𝗧𝗢𝗗𝗢𝗦 𝗟𝗢𝗦 𝗦𝗘𝗥𝗩𝗜𝗖𝗜𝗢𝗦

💎 Más de 150 servicios disponibles
⚡ Consultas rápidas y precisas
🛡️ Plataforma segura y estable
🚀 Tecnología de última generación
📡 Actualizaciones constantes
🎯 Respuesta en pocos segundos

━━━━━━━━━━━━━━━━━━━━━━━

🔎 𝗖𝗢𝗡𝗘𝗖𝗧𝗔 𝗟𝗔 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗖𝗜Ó𝗡
📂 Descubre relaciones y encuentra
los datos que necesitas desde un
solo lugar.

━━━━━━━━━━━━━━━━━━━━━━━

👇 𝗦𝗘𝗟𝗘𝗖𝗖𝗜𝗢𝗡𝗔 𝗨𝗡𝗔 𝗖𝗔𝗧𝗘𝗚𝗢𝗥Í𝗔 👇"""

    await update.message.reply_text(texto, reply_markup=teclado)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Botón volver
    if query.data == "volver_cmds":
        teclado = InlineKeyboardMarkup([
            [
    InlineKeyboardButton("╔═ 🪪 RENIEC ═╗", callback_data="cmd_reniec"),
    InlineKeyboardButton("╔═ 🏢 RUC ═╗", callback_data="cmd_ruc")
],
[
    InlineKeyboardButton("╔═ 🚘 VEHÍCULOS ═╗", callback_data="cmd_vehiculos"),
    InlineKeyboardButton("╔═ 📱 TELÉFONO ═╗", callback_data="cmd_telefono")
],
[
    InlineKeyboardButton("╔═ ⚖️ DENUNCIAS ═╗", callback_data="cmd_denuncia"),
    InlineKeyboardButton("╔═ 💰 SUELDO ═╗", callback_data="cmd_sueldo")
],
[
    InlineKeyboardButton("╔═ 🧬 FACIAL ═╗", callback_data="cmd_facial"),
    InlineKeyboardButton("╔═ 💎 COMPRAR ═╗", callback_data="cmd_buy")
]
        ])

        texto = f"""╔══════════════════════╗
        ⚜️ 𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦 𝗣𝗘𝗥𝗨 ⚜️
╚════════════════════════╝

🚀 𝗟𝗔 𝗣𝗟𝗔𝗧𝗔𝗙𝗢𝗥𝗠𝗔 #𝟭 𝗗𝗘 𝗖𝗢𝗡𝗦𝗨𝗟𝗧𝗔𝗦

━━━━━━━━━━━━━━━━━━━━━━━

🛰️ 𝗔𝗖𝗖𝗘𝗗𝗘 𝗔 𝗧𝗢𝗗𝗢𝗦 𝗟𝗢𝗦 𝗦𝗘𝗥𝗩𝗜𝗖𝗜𝗢𝗦

💎 Más de 150 servicios disponibles
⚡ Consultas rápidas y precisas
🛡️ Plataforma segura y estable
🚀 Tecnología de última generación
📡 Actualizaciones constantes
🎯 Respuesta en pocos segundos

━━━━━━━━━━━━━━━━━━━━━━━

🔎 𝗖𝗢𝗡𝗘𝗖𝗧𝗔 𝗟𝗔 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗖𝗜Ó𝗡
📂 Descubre relaciones y encuentra
los datos que necesitas desde un
solo lugar.

━━━━━━━━━━━━━━━━━━━━━━━

👇 𝗦𝗘𝗟𝗘𝗖𝗖𝗜𝗢𝗡𝗔 𝗨𝗡𝗔 𝗖𝗔𝗧𝗘𝗚𝗢𝗥Í𝗔 👇"""

        await query.edit_message_text(
            texto,
            reply_markup=teclado
        )
        return

    comandos = {
        "cmd_reniec": """❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨 ❱ ➾ RENIEC
✦ ──────────────── ✦
ᴄᴏᴍᴀɴᴅᴏs ᴅɪsᴘᴏɴɪʙʟᴇs ➾ 5
ᴘᴀɢɪɴᴀ ➾ 1/1

1. DNI TARJETA
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /dnit 44445555
• ᴘʀᴇᴄɪᴏ ➾ 5 ᴄʀᴇ́ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ texto con foto y firma

2. DNI POR NOMBRES
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /nm juan quispe
• ᴘʀᴇᴄɪᴏ ➾ 6 ᴄʀᴇ́ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ dni por nombre y apellido

3. DNI SIMPLE
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /dni 44445555
• ᴘʀᴇᴄɪᴏ ➾ 4 ᴄʀᴇ́ᴅɪᴛᴏs

Página: 1/1""",

        "cmd_ruc": "Uso: /ruc 20538856674",

        "cmd_vehiculos": f"""❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨 ❱ ➾ VEHICULARES
✦ ──────────────── ✦

1. PLACA TEXTO
• ᴄᴏᴍᴀɴᴅᴏ ➾ /placa ABC123
• ᴘʀᴇᴄɪᴏ ➾ {PRECIOS['placa']} créditos

2. SOAT VIGENTE
• ᴄᴏᴍᴀɴᴅᴏ ➾ /hsoat ABC123
• ᴘʀᴇᴄɪᴏ ➾ {PRECIOS['hsoat']} créditos

3. DENUNCIAS POR PLACA
• ᴄᴏᴍᴀɴᴅᴏ ➾ /denpla ABC123
• ᴘʀᴇᴄɪᴏ ➾ {PRECIOS['denpla']} créditos""",

        "cmd_telefono": f"""❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨 ❱ ➾ TELEFONIA

1. TELX POR DNI
• ᴄᴏᴍᴀɴᴅᴏ ➾ /telp 44445555
• ᴘʀᴇᴄɪᴏ ➾ {PRECIOS['telp']} créditos

2. TELX POR NUMERO
• ᴄᴏᴍᴀɴᴅᴏ ➾ /telpcel 999888777
• ᴘʀᴇᴄɪᴏ ➾ {PRECIOS['telpcel']} créditos""",

        "cmd_denuncia": f"""❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨   ❱ ➾ DENUNCIA
✦ ──────────────── ✦
ᴄᴏᴍᴀɴᴅᴏs ᴅɪsᴘᴏɴɪʙʟᴇs ➾ 2
ᴘᴀ́ɢɪɴᴀ ➾ 1/1

1. DENUNCIAS EN PDF
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /denuncias 44445555
• ᴘʀᴇᴄɪᴏ ➾ 30 ᴄʀᴇ́ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ Lista de denuncias en PDF

2. DENUNCIAS POR DNI
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /den 12345678
• ᴘʀᴇᴄɪᴏ ➾ 15 ᴄʀᴇ́ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ Consulta denuncias asociadas a un DNI.




Página: 1/1""",

        "cmd_sueldo": f"""❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨 ❱ ➾ SUELDOS
✦ ──────────────── ✦
ᴄᴏᴍᴀɴᴅᴏs ᴅɪsᴘᴏɴɪʙʟᴇs ➾ 1
ᴘᴀ́ɢɪɴᴀ ➾ 1/1

1. CONSULTA DE SUELDOS
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /suel 12345678
• ᴘʀᴇᴄɪᴏ ➾ 4 ᴄʀᴇ́ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ Información de sueldos registrados

Página: 1/1""",
        "cmd_buy": f"""╔════════════════════╗
      💎 PLANES PREMIUM 💎
╚════════════════════╝

💰 𝗖𝗥É𝗗𝗜𝗧𝗢𝗦

🥉 100 Créditos ➜ S/ 10
🥈 200 Créditos ➜ S/ 20
🥇 400 Créditos ➜ S/ 30
💠 500 Créditos ➜ S/ 40
🚀 800 Créditos ➜ S/ 50
👑 2,000 Créditos ➜ S/ 100
💎 4,300 Créditos ➜ S/ 200

━━━━━━━━━━━━━━━━━━

♾️ 𝗜𝗟𝗜𝗠𝗜𝗧𝗔𝗗𝗢𝗦

💥 7 DÍAS ➜ S/ 20
⚡ 15 DÍAS ➜ S/ 35
🔱 30 DÍAS ➜ S/ 60
👑 60 DÍAS ➜ S/ 100

━━━━━━━━━━━━━━━━━━

💳 Aceptamos:
🏦 Yape • Plin • Bcp

╭━━━〔 💠 𝗣𝗔𝗚𝗢𝗦 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 💠 〕━━━╮

⚡ Para activar tu compra o recargar
tu cuenta, comunícate con:

👤 ➤ @Xxxxxxx_Gatito_xxxxxxx

✦ Atención rápida
✦ Activación inmediata
✦ Soporte personalizado

╰━━━━━━━━━━━━━━━━━━━━━━╯""" 
}


    if query.data in comandos:
        volver = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Volver al inicio", callback_data="volver_cmds")]
        ])
        await query.edit_message_text(
            comandos[query.data],
            reply_markup=volver
        )


    elif query.data == "cmd_facial":
        await query.edit_message_text("""❰ #𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦_𝗗𝗔𝗧𝗔_𝗣𝗘𝗥𝗨 ❱ ➾ FACIAL
✦ ──────────────── ✦

ᴄᴏᴍᴀɴᴅᴏs ᴅɪsᴘᴏɴɪʙʟᴇs ➾ 1
ᴘᴀ‌ɢɪɴᴀ ➾ 1/1

1. RECONOCIMIENTO FACIAL
• ᴇsᴛᴀᴅᴏ ➾ OPERATIVO [✅]
• ᴄᴏᴍᴀɴᴅᴏ ➾ /facial
• ᴘʀᴇᴄɪᴏ ➾ 30 ᴄʀᴇ‌ᴅɪᴛᴏs
• ʀᴇsᴜʟᴛᴀᴅᴏ ➾ Procesamiento de imagen facial

✦ ──────────────── ✦

Página: 1/1""")

    elif query.data == "cmd_buy":
        await query.edit_message_text(comandos["cmd_buy"])

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios()
    if user_id in usuarios: return await update.message.reply_text("Ya estas registrado")
    usuarios[user_id] = {"creditos": 0, "nombre": update.effective_user.first_name, "username": update.effective_user.username, "fecha_registro": get_fecha(), "rol": "PENDIENTE", "plan": "FREE"}
    guardar_usuarios(usuarios)
    await update.message.reply_text(f"Registro exitoso! Bienvenido {update.effective_user.first_name}")

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios()
    usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    u = usuarios.get(user_id, {})
    texto = f"""[#BOT DATA] ➾ PERFIL DE USUARIO
PERFIL DE ➾ {u.get("nombre", "Usuario")}
[🙎‍♂️] ID ➾ {user_id}
[👨🏻‍💻] USER ➾ @{u.get("username", "")}
[💰] CREDITOS ➾ {u.get('creditos', 0)}
[📊] CONSULTAS ➾ {u.get('consultas', 0)}"""
    await update.message.reply_text(texto)



async def denuncias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Uso: /denuncias <DNI>")
        return

    dni = context.args[0]

    if not dni.isdigit() or len(dni) != 8:
        await update.message.reply_text("❌ El DNI debe tener 8 dígitos.")
        return

    url = f"https://api-codart.cgrt.org/api/v1/consultas/fd/denuncias/{dni}"

    try:
        data = await consultar_api_get(url)

        if not data.get("success"):
            await update.message.reply_text("❌ No se encontraron denuncias.")
            return

        info = data["data"]

        await update.message.reply_text(
            f"📂 Se encontraron {info['cantidad_denuncias']} denuncia(s).\n"
            f"Enviando archivos..."
        )

        for den in info["denuncias"]:
            pdf = den["data_uri"].split(",")[1]
            archivo = BytesIO(base64.b64decode(pdf))
            archivo.name = den["nombre"]

            caption = (
                f"🚨 <b>DENUNCIA #{den['numero']}</b>\n"
                f"👤 <b>Tipo:</b> {den['tipo']}\n"
                f"🏢 <b>Comisaría:</b> {den['comisaria']}\n"
                f"📄 <b>Orden:</b> {den['n_orden']}\n"
                f"📅 <b>Hecho:</b> {den['f_hecho']}\n"
                f"📝 <b>Registro:</b> {den['f_registro']}"
            )

            await update.message.reply_document(
                document=archivo,
                filename=den["nombre"],
                caption=caption,
                parse_mode="HTML"
            )

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"""╔════════════════════╗
      💎 PLANES PREMIUM 💎
╚════════════════════╝

💰 𝗖𝗥É𝗗𝗜𝗧𝗢𝗦

🥉 100 Créditos ➜ S/ 10
🥈 200 Créditos ➜ S/ 20
🥇 400 Créditos ➜ S/ 30
💠 500 Créditos ➜ S/ 40
🚀 800 Créditos ➜ S/ 50
👑 2,000 Créditos ➜ S/ 100
💎 4,300 Créditos ➜ S/ 200

━━━━━━━━━━━━━━━━━━

♾️ 𝗜𝗟𝗜𝗠𝗜𝗧𝗔𝗗𝗢𝗦

💥 7 DÍAS ➜ S/ 20
⚡ 15 DÍAS ➜ S/ 35
🔱 30 DÍAS ➜ S/ 60
👑 60 DÍAS ➜ S/ 100

━━━━━━━━━━━━━━━━━━

💳 Aceptamos:
🏦 Yape • Plin • Bcp

╭━━━〔 💠 𝗣𝗔𝗚𝗢𝗦 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 💠 〕━━━╮

⚡ Para activar tu compra o recargar
tu cuenta, comunícate con:

👤 ➤ @Xxxxxxx_Gatito_xxxxxxx

✦ Atención rápida""
✦ Activación inmediata
✦ Soporte personalizado

╰━━━━━━━━━━━━━━━━━━━━━━╯""")

async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""╔═════════════════════╗
        👑 𝗦𝗧𝗔𝗙𝗙 𝗢𝗙𝗜𝗖𝗜𝗔𝗟 👑
╚════════════════════╝

🛡️ 𝗔𝗗𝗠𝗜𝗡𝗜𝗦𝗧𝗥𝗔𝗗𝗢𝗥 𝗣𝗥𝗜𝗡𝗖𝗜𝗣𝗔𝗟

👤 Usuario:
➜ @Xxxxxxx_Gatito_xxxxxxx

━━━━━━━━━━━━━━━━━━━━━━

⚡ Servicios disponibles:
• 💳 Venta de créditos
• ♾️ Planes ilimitados
• 🛠️ Soporte técnico
• 📞 Atención personalizada

━━━━━━━━━━━━━━━━━━━━━━

💬 Para compras, soporte o consultas,
contacta directamente al administrador.

🚀 Gracias por confiar en
⚜️ 𝗦𝗜𝗦𝗧𝗘𝗠𝗔𝗦 𝗗𝗔𝗧𝗔 𝗣𝗘𝗥𝗨 ⚜️""", parse_mode="HTML")

async def quitarcrd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_ID:
        return await update.message.reply_text("""╔══════════════════════╗
        🚫 ACCESO DENEGADO 🚫
╚══════════════════════╝

⚠️ No cuentas con los permisos
necesarios para ejecutar este comando.

🔒 El comando <code>/quitarcrd</code> está
reservado exclusivamente para el
personal autorizado.

━━━━━━━━━━━━━━━━━━━━━━

👑 Si crees que se trata de un error,
contacta al administrador:

➜ @Xxxxxxx_Gatito_xxxxxxx""", parse_mode="HTML")
    if len(context.args) < 2:
        return await update.message.reply_text("Uso: /quitarcrd ID_USUARIO CANTIDAD")
    target_id = context.args[0]
    try:
        cantidad = int(context.args[1])
    except:
        return await update.message.reply_text("La cantidad debe ser un número")
    usuarios = cargar_usuarios()
    if target_id not in usuarios:
        return await update.message.reply_text(f"El usuario {target_id} no existe en la BD")
    saldo_anterior = usuarios[target_id]["creditos"]
    usuarios[target_id]["creditos"] -= cantidad
    if usuarios[target_id]["creditos"] < 0:
        usuarios[target_id]["creditos"] = 0
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ CREDITOS QUITADOS
[👤] USUARIO ➾ {target_id}
[➖] QUITADOS ➾ {cantidad} Créditos
[💰] SALDO ANTERIOR ➾ {saldo_anterior}
[💰] SALDO ACTUAL ➾ {usuarios[target_id]['creditos']}"""
    await update.message.reply_text(texto)

async def addcreditos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_ID: return await update.message.reply_text("""╔══════════════════════╗
        🚫 ACCESO DENEGADO 🚫
╚══════════════════════╝

⚠️ No cuentas con los permisos
necesarios para ejecutar este comando.

🔒 El comando <code>/addcreditos</code> está
reservado exclusivamente para el
personal autorizado.

━━━━━━━━━━━━━━━━━━━━━━
                                                                       

👑 Si desea usar este comando contacte con el administrador:

➜ @Xxxxxxx_Gatito_xxxxxxx""", parse_mode="HTML")
    if len(context.args)!= 2: return await update.message.reply_text("""╔══════════════════════╗
      💎 AÑADIR CRÉDITOS 💎
╚══════════════════════╝

📝 Uso del comando:

<code>/addcreditos ID CANTIDAD</code>

📌 Ejemplo:
<code>/addcreditos 123456789 100</code>

━━━━━━━━━━━━━━━━━━━━━━

👤 ID ➜ ID numérico del usuario.
💳 CANTIDAD ➜ Créditos a agregar.

⚠️ Comando exclusivo para administradores.""", parse_mode="HTML")
    target_id, cantidad = context.args[0], int(context.args[1])
    usuarios = cargar_usuarios()
    if target_id not in usuarios: return await update.message.reply_text(f"El usuario {
     target_id} no existe en la base de datos.")
    saldo_anterior = usuarios[target_id]["creditos"]
    usuarios[target_id]["creditos"] += cantidad
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ CREDITOS AGREGADOS
[👤] USUARIO ➾ {target_id
                }
[➕] AGREGADOS ➾ {cantidad} Créditos
[💰] SALDO ANTERIOR ➾ {saldo_anterior}
[💰] SALDO ACTUAL ➾ {usuarios[target_id]['creditos']}"""
    await update.message.reply_text(texto)

# ----------------------
# FUNCIÓN CORREGIDA
# ----------------------

async def facial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Volver", callback_data="volver_cmds")]
    ])

    # 1. ARREGLO: Acepta foto con caption O foto sola
    message = update.message
    if not message or not message.photo:
        await message.reply_text(
            """
╔═════════════════╗
      🧬 COMANDO FACIAL
╚═════════════════╝

❌ No se recibió ninguna imagen.

📌 Uso correcto:
📷 Envía la foto y pon /facial 
   en la descripción de la foto.

━━━━━━━━━━━━━━━━━━━
⚡ SISTEMA FACIAL ONLINE
""",
            reply_markup=keyboard
        )
        return

    try:
        await message.reply_text(
            """
╔═════════════════╗
    🧬 ESCÁNER FACIAL
╚═════════════════╝

🔄 Procesando imagen...
🛰 Conectando al sistema...
⚙️ Analizando coincidencias...

━━━━━━━━━━━━━━━━━━━
""",
            reply_markup=keyboard
        )

        # 2. ARREGLO: Descargar bien y con nombre correcto
        photo = message.photo[-1] # máxima calidad
        file = await context.bot.get_file(photo.file_id)
        imagen_bytes = await file.download_as_bytearray()

        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Accept": "application/json"
        }

        # 3. ARREGLO: El nombre del campo debe coincidir con la API
        # Muchas APIs piden "image" o "file", no "image_facial"
        files = {
            "image": ("imagen.jpg", bytes(imagen_bytes), "image/jpeg") 
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api-codart.cgrt.org/api/v1/consultas/fd/facial/top",
                headers=headers,
                files=files
            )
            
            # Para debug: si falla, muestra el error real de la API
            if response.status_code != 200:
                await message.reply_text(f"Error API: {response.status_code}\n{response.text}")
                return
                
            data = response.json()

        if not data.get("success"):
            await message.reply_text(
                """
╔═══════════════╗
     🧬 RESULTADO FACIAL
╚═══════════════╝

❌ No se encontraron coincidencias.
""",
                reply_markup=keyboard
            )
            return

        info = data["data"]
        texto = f"""
╔═════════════════╗
     🧬 RESULTADO FACIAL
╚═════════════════╝

✅ Análisis completado

🔎 Tipo: {info.get('tipo_resultado','N/A')}
👥 Coincidencias: {info.get('coincidencias_mostradas',0)}

━━━━━━━━━━━━━━━━━━━
"""

        for i, p in enumerate(info.get("coincidencias", []), 1):
            texto += f"""
👤 COINCIDENCIA #{i}

🪪 DNI: <code>{p.get('dni','N/A')}</code>
📛 Nombre: {p.get('nombre','N/A')}
🎯 Similitud: {p.get('porcentaje','0')}%

━━━━━━━━━━━━━━━━━━━
"""

        texto += "\n⚡ CYBER DATA PERÚ"
        await message.reply_text(texto, parse_mode="HTML", reply_markup=keyboard)

    except httpx.RequestError as e:
        await message.reply_text(f"⚠️ Error de conexión: {e}", reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}", reply_markup=keyboard)
async def telpcel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    usuarios = cargar_usuarios()
    usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})

    ok, msg = await validar_creditos(user_id, "telpcel", usuarios)
    if not ok:
        return await update.message.reply_text(msg)

    if not context.args:
        return await update.message.reply_text(
            "❌ <b>Uso correcto:</b>\n<code>/telpcel 900000001</code>",
            parse_mode="HTML"
        )

    numero = context.args[0]

    if not (numero.isdigit() and len(numero) == 9):
        return await update.message.reply_text(
            "❌ El número debe contener exactamente 9 dígitos."
        )

    try:
        data = await consultar_api_get (
            f"https://api-codart.cgrt.org/api/v1/consultas/fd/telp/cel/{numero}"
        )

        if not data.get("success"):
            return await update.message.reply_text(
                "❌ No se encontraron resultados."
            )

        titulares = data["data"]["titulares"]

        texto = """╔═════════════════════╗
📡 <b>TELP CEL • SISTEMA</b>
╚═════════════════════╝

🟢 <b>ESTADO DEL SISTEMA</b>
➜ ONLINE

⚡━━━━━━━━━━━━━━━━━━━━━━⚡
"""

        for t in titulares:
            texto += f"""
👤 <b>TITULAR</b>
➜ <code>{t.get('titular','-')}</code>

📱 <b>TELÉFONO</b>
➜ <code>{t.get('telefono','-')}</code>

🏢 <b>OPERADOR</b>
➜ <code>{t.get('operador','-')}</code>

🪪 <b>DNI / RUC</b>
➜ <code>{t.get('dni_ruc','-')}</code>

💳 <b>PLAN</b>
➜ <code>{t.get('plan','-')}</code>

📧 <b>CORREO</b>
➜ <code>{t.get('correo','-')}</code>

🏛️ <b>EMPRESA</b>
➜ <code>{t.get('empresa','-')}</code>

⚡━━━━━━━━━━━━━━━━━━━━━━⚡
"""

        texto += """
🚀 <b>Consulta completada correctamente</b>

⚜️ <b>SISTEMAS DATA PERU</b>
📡 Powered by CODART X API V1
"""

        botones = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "VOLVER AL MENU",
                    callback_data="volver_cmds"
                )
            ]
        ])

        await update.message.reply_text(
            texto,
            parse_mode="HTML",
            reply_markup=botones
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Error:</b>\n<code>{e}</code>",
            parse_mode="HTML"
        )
async def dni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "dni", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /dni 12345678")
    dni_num = context.args[0]
    m = await update.message.reply_text("🔎 Consultando DNI... -4 creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/dni/{dni_num}"
    data = await consultar_api_get(url)
    if "error" in data: return await m.edit_text(f"Error: {data['error']}")
    if not data.get("success"): return await m.edit_text(f"Error: {data.get('message','DNI no encontrado')}")
    res = data.get("data", {}); d = res.get("dni", {}); n = res.get("nacimiento", {}); dom = res.get("domicilio", {}); info = res.get("informacion_general", {})
    usuarios[user_id]["creditos"] -= PRECIOS["dni"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ CONSULTA DNI
[🆔] DNI: {d.get('completo')}
[👤] Nombre: {res.get('nombres')} {res.get('apellidos')}
[⚧] Genero: {res.get('genero')}
[📅] Nac: {n.get('fecha')} | {n.get('edad')}
[🏠] Dir: {dom.get('direccion')} - {dom.get('distrito')}
[👨] Padre: {info.get('padre')}
[👩] Madre: {info.get('madre')}
💰 Creditos: {usuarios[user_id]['creditos']}"""
    await m.edit_text(texto)

async def dnit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "dnit", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /dnit 12345678")
    dni_num = context.args[0]
    m = await update.message.reply_text(f"🔎 Consultando DNI-T de {dni_num}... -{PRECIOS['dnit']} creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/dnit/{dni_num}"
    data = await consultar_api_get(url)
    if "error" in data: return await m.edit_text(f"Error: {data['error']}")
    if not data.get("success"): return await m.edit_text(f"Error: {data.get('message','DNI no encontrado')}")
    res = data.get("data", {})
    d = res.get("dni", {}); n = res.get("nacimiento", {}); dom = res.get("domicilio", {}); info = res.get("informacion_general", {})
    images = res.get("images", [])
    usuarios[user_id]["creditos"] -= PRECIOS["dnit"]
    usuarios[user_id] = {"consultas": 0}
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ DNI-T
[🆔] DNI ➾ {d.get('completo')}
[👤] NOMBRE ➾ {res.get('nombres')} {res.get('apellidos')}
[⚧] GENERO ➾ {res.get('genero')}
[📅] NACIMIENTO ➾ {n.get('fecha')} | {n.get('edad')}
[🏠] DIRECCION ➾ {dom.get('direccion')}
[📚] EDUCACION ➾ {info.get('nivel_educativo')}
[💍] ESTADO CIVIL ➾ {info.get('estado_civil')}
[📄] EMISION ➾ {info.get('fecha_emision')} | CADUCA ➾ {info.get('fecha_caducidad')}
💰 Creditos: {usuarios[user_id]['creditos']}"""
    await m.edit_text(texto)
    for i, img_data in enumerate(images, 1):
        try:
            base64_str = img_data.get('data_uri', '').split(',')[1]
            img_bytes = base64.b64decode(base64_str)
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=io.BytesIO(img_bytes), caption=f"Foto {i} de {d.get('completo')}")
        except:
            pass

async def hsoat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "hsoat", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /hsoat ABC123")
    placa = context.args[0].upper()
    m = await update.message.reply_text(f"🔎 Consultando HSOAT de {placa}... -{PRECIOS['hsoat']} creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/hsoat/{placa}"
    data = await consultar_api_get(url)
    if "error" in data: return await m.edit_text(f"Error: {data['error']}")
    if not data.get("success"): return await m.edit_text(f"Error: {data.get('message','Placa no encontrada')}")
    res = data.get("data", {})
    placa_data = res.get("placa"); cantidad = res.get("cantidad_registros"); historial = res.get("historial", [])
    usuarios[user_id]["creditos"] -= PRECIOS["hsoat"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ HSOAT
[🚗] PLACA ➾ {placa_data}
[📊] REGISTROS ➾ {cantidad}"""
    for i, h in enumerate(historial, 1):
        texto += f"\n\n--- SOAT {i} ---\n[🏢] COMPAÑIA ➾ {h.get('compania')}\n[✅] ESTADO ➾ {h.get('estado')}\n[📄] PÓLIZA ➾ {h.get('poliza')}"
    texto += f"\n\n💰 Creditos: {usuarios[user_id]['creditos']}"
    await m.edit_text(texto)

async def denpla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "denpla", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /denpla ABC123")
    placa = context.args[0].upper()
    m = await update.message.reply_text(f"🔎 Consultando DENUNCIAS de {placa}... -{PRECIOS['denpla']} creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/denpla/{placa}"
    data = await consultar_api_get(url)
    if "error" in data: return await m.edit_text(f"Error: {data['error']}")
    if not data.get("success"): return await m.edit_text(f"Error: {data.get('message','Placa no encontrada')}")
    res = data.get("data", {})
    placa_data = res.get("placa"); cantidad = res.get("cantidad_denuncias"); denuncias = res.get("denuncias", [])
    usuarios[user_id]["creditos"] -= PRECIOS["denpla"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ DENUNCIAS POLICIALES
[🚗] PLACA ➾ {placa_data}
[🚨] TOTAL DENUNCIAS ➾ {cantidad}"""
    for d in denuncias:
        texto += f"\n\n--- DENUNCIA {d.get('numero')} ---\n[📌] TIPO ➾ {d.get('tipo')}\n[🏛️] COMISARIA ➾ {d.get('comisaria')}"
    texto += f"\n\n💰 Creditos: {usuarios[user_id]['creditos']}"
    await m.edit_text(texto)

async def suel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    usuarios = cargar_usuarios()
    usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})

    ok, msg = await validar_creditos(user_id, "suel", usuarios)
    if not ok:
        return await update.message.reply_text(msg)

    if not context.args:
        return await update.message.reply_text("Uso: /suel 12345678")

    dni_num = context.args[0]

    m = await update.message.reply_text("💼 Consultando sueldos... -4 créditos")

    url = f"{BASE_URL}/api/v1/consultas/fd/suel/{dni_num}"
    data = await consultar_api_get(url)

    if "error" in data:
        return await m.edit_text(f"❌ Error: {data['error']}")

    if not data.get("success"):
        return await m.edit_text(f"❌ Error: {data.get('message','No se encontraron registros')}")

    res = data.get("data", {})
    sueldos = res.get("sueldos", [])

    if not sueldos:
        return await m.edit_text("❌ No se encontraron registros.")

    usuarios[user_id]["creditos"] -= PRECIOS["suel"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)

    texto = f"""<b>[#BOT DATA] ➾ CONSULTA SUELDOS</b>

🆔 <b>DNI:</b> {res.get("consulta")}
📋 <b>Total Registros:</b> {res.get("total_registros")}

"""

    for i, s in enumerate(sueldos, start=1):
        texto += f"""
<b>══════════════════════</b>
<b>Registro {i}</b>

🏢 <b>Empresa:</b> {s.get("empresa")}
🪪 <b>RUC:</b> {s.get("ruc")}
📅 <b>Periodo:</b> {s.get("periodo")}
👔 <b>Situación:</b> {s.get("situacion")}
💰 <b>Sueldo:</b> {s.get("sueldo")}
"""

    texto += f"""

══════════════════════
💳 <b>Créditos:</b> {usuarios[user_id]["creditos"]}
"""

    await m.edit_text(texto, parse_mode="HTML")

async def telp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios(); usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    ok, msg = await validar_creditos(user_id, "telp", usuarios)
    if not ok: return await update.message.reply_text(msg)
    if not context.args: return await update.message.reply_text("Uso: /telp 12345678")
    dni_num = context.args[0]
    m = await update.message.reply_text(f"🔎 Consultando TELÉFONOS de {dni_num}... -{PRECIOS['telp']} creditos")
    url = f"{BASE_URL}/api/v1/consultas/fd/telp/{dni_num}"
    data = await consultar_api_get(url)
    if "error" in data: return await m.edit_text(f"Error: {data['error']}")
    if not data.get("success"): return await m.edit_text(f"Error: {data.get('message','DNI no encontrado')}")
    res = data.get("data", {})
    lineas = res.get("lineas", []); cantidad = res.get("lineas_encontradas")
    usuarios[user_id]["creditos"] -= PRECIOS["telp"]
    usuarios[user_id]["consultas"] += 1
    guardar_usuarios(usuarios)
    texto = f"""[#BOT DATA] ➾ TELEFONOS
[🆔] DNI ➾ {dni_num}
[📞] LINEAS ENCONTRADAS ➾ {cantidad}"""
    for i, l in enumerate(lineas, 1):
        periodo = l.get('periodo')
        periodo_fmt = f"{periodo[4:6]}/{periodo[:4]}" if periodo and len(periodo)==6 else periodo
        texto += f"\n\n--- LINEA {i} ---\n[📱] NUMERO ➾ {l.get('telefono')}\n[📡] OPERADOR ➾ {l.get('operador')}"
    texto += f"\n\n💰 Creditos: {usuarios[user_id]['creditos']}"
    await m.edit_text(texto)

#... aqui van tus otros comandos: placa, agv, denuncia, nm, telpcel

# ===== MAIN =====
def main():
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cmds", cmds))
    application.add_handler(CommandHandler("suel", suel))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("me", me))
    application.add_handler(CommandHandler("suel", suel))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("staff", staff))
    application.add_handler(CommandHandler("addcreditos", addcreditos))
    application.add_handler(CommandHandler("quitarcrd", quitarcrd))
    application.add_handler(CommandHandler("dni", dni))
    application.add_handler(CommandHandler("dnit", dnit))
    application.add_handler(CommandHandler("hsoat", hsoat))
    application.add_handler(CommandHandler("denpla", denpla))
    application.add_handler(CommandHandler("telp", telp))
    application.add_handler(CommandHandler("den", den))
    application.add_handler(CommandHandler("telpcel", telpcel))
    application.add_handler(CommandHandler("facial", facial))
    application.add_handler(MessageHandler(filters.PHOTO & filters.COMMAND, facial)) #
    application.add_handler(CommandHandler("denuncias", denuncias))
    # agrega los demas handlers aqui
    print("Bot iniciado v2.1...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()