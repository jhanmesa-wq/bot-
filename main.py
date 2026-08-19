import asyncio
import base64
import datetime
import html
import io
import json
import logging
import os
import re
from io import BytesIO
from threading import Thread
from typing import Any, Dict, Optional, Tuple
import httpx
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
ApplicationBuilder,
CallbackQueryHandler,
CommandHandler,
ContextTypes,
MessageHandler,
filters,
)
from flask import Flask, request, jsonify
#============================================================
#LOGGING
#============================================================
logging.basicConfig(
format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
level=logging.INFO,
)
logger = logging.getLogger("specter_peru")
#============================================================
#CONFIGURACIÓN
#============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
ARCHIVO_USUARIOS = os.getenv("ARCHIVO_USUARIOS") or "usuarios.json"
BASE_URL = os.getenv("BASE_URL") or "https://api-codart.cgrt.org"
BOT_USER = "@specter_Dox44bot"
BOT_NAME = "⚜ SPECTER PERÚ ⚜"
CLAVE_SECRETA = os.getenv("CLAVE_SECRETA", "PON_TU_CLAVE_AQUI")
TASA_CREDITOS = 1
TU_CELULAR_YAPE = "925805734"
TU_NOMBRE = "CHRISTIAN GUSTAVO RAMOS GONZALES"
ADMIN_ID = {
item.strip()
for item in (os.getenv("ADMIN_ID") or "").split(",")
if item.strip()
}
#Precios actualizados y nuevos comandos agregados
PRECIOS = {
"dni": 4,
"agv": 20,
"telpcel": 15,
"facial": 30,
"ruc": 5,
"suel": 5,
"denuncia": 10,
"placa": 12,
"nm": 6,
"hsoat": 8,
"denpla": 30,
"dnit": 5,
"telp": 15,
"revtec": 10,
"dir": 6,
"dnivel": 10,
"rqh": 30,
"denuncias": 30
}
#============================================================
#FLASK KEEP-ALIVE & WEBHOOK PAGO
#============================================================

app = Flask(__name__)
@app.route('/')
def home():
return "🔥 SPECTER PERÚ BOT ACTIVO 24/7"
@app.route('/health')
def health():
return "OK", 200
@app.route("/webhook-pagos/", methods=["POST"])
def recibir_pago():
datos = request.get_json()
if not datos:
return jsonify({"error": "Sin datos"}), 400
code
Code
celular = str(datos.get("numero", "")).strip()
monto_str = str(datos.get("monto", "0"))
remitente = datos.get("de", "Desconocido")

try:
    monto = float(monto_str.replace(",", "."))
except:
    return jsonify({"error": "Monto inválido"}), 400

creditos = int(monto * TASA_CREDITOS)
usuarios = cargar_usuarios()
user_id_encontrado = None

for user_id, info in usuarios.items():
    if str(info.get("celular", "")).strip() == celular:
        user_id_encontrado = user_id
        break

if user_id_encontrado and creditos > 0:
    usuarios[user_id_encontrado]["creditos"] = int(usuarios[user_id_encontrado].get("creditos", 0)) + creditos
    guardar_usuarios(usuarios)
    # Notificación asíncrona mediante un thread para no bloquear Flask
    Thread(target=lambda: asyncio.run(notificar_usuario(user_id_encontrado, monto, creditos, remitente))).start()
    logger.info(f"✅ PAGO — S/{monto} de {remitente} → +{creditos} créditos a {user_id_encontrado}")
else:
    logger.warning(f"⚠️ Pago S/{monto} de {remitente} — Usuario NO REGISTRADO: {celular}")

return jsonify({"status": "ok"}), 200
def run_flask():
port = int(os.environ.get("PORT", 8080))
app.run(host='0.0.0.0', port=port)
def keep_alive():
t = Thread(target=run_flask)
t.daemon = True
t.start()
#============================================================
#ESTILO FUTURISTA CENTRALIZADO
#============================================================
SEPARADOR = "━━━━━━━━━━━━━━━━━━━━━━"
SEPARADOR_CORTO = "━━━━━━━━━━━━━━━━━━"
BTN_VOLVER = InlineKeyboardMarkup(
[[InlineKeyboardButton("🏠 VOLVER AL MENÚ", callback_data="volver_cmds")]]
)
def menu_teclado() -> InlineKeyboardMarkup:
return InlineKeyboardMarkup(
[
[
InlineKeyboardButton("🪪 RENIEC", callback_data="cmd_reniec"),
InlineKeyboardButton("🏢 RUC", callback_data="cmd_ruc"),
],
[
InlineKeyboardButton("🚘 VEHÍCULOS", callback_data="cmd_vehiculos"),
InlineKeyboardButton("📱 TELÉFONO", callback_data="cmd_telefono"),
],
[
InlineKeyboardButton("⚖️ DENUNCIAS", callback_data="cmd_denuncia"),
InlineKeyboardButton("💰 SUELDOS", callback_data="cmd_sueldo"),
],
[
InlineKeyboardButton("🧬 FACIAL", callback_data="cmd_facial"),
InlineKeyboardButton("🔍 OTROS", callback_data="cmd_otros"),
],
[
InlineKeyboardButton("💎 COMPRAR", callback_data="cmd_buy"),
]
]
)
def titulo_sistema(nombre: str, icono: str = "⚡") -> str:
return (
f"╔═════════════════════╗\n"
f"{icono} <b>{html.escape(nombre.upper())}</b>\n"
f"╚═════════════════════╝"
)
def error_html(texto: Any) -> str:
if texto is None: return "-"
return html.escape(str(texto))
#============================================================
#BASE DE DATOS DE USUARIOS
#============================================================
def cargar_usuarios() -> Dict[str, Dict[str, Any]]:
try:
if not os.path.exists(ARCHIVO_USUARIOS):
return {}
with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as archivo:
data = json.load(archivo)
return data if isinstance(data, dict) else {}
except (OSError, json.JSONDecodeError, TypeError) as exc:
logger.warning("No se pudo cargar usuarios: %s", exc)
return {}
def guardar_usuarios(data: Dict[str, Dict[str, Any]]) -> None:
directorio = os.path.dirname(os.path.abspath(ARCHIVO_USUARIOS))
if directorio:
os.makedirs(directorio, exist_ok=True)
temporal = f"{ARCHIVO_USUARIOS}.tmp"
with open(temporal, "w", encoding="utf-8") as archivo:
json.dump(data, archivo, indent=4, ensure_ascii=False)
os.replace(temporal, ARCHIVO_USUARIOS)
def get_fecha() -> str:
return datetime.datetime.now().strftime("%d/%m/%Y - %I:%M:%S %p")
def obtener_usuario(update: Update, usuarios: Dict[str, Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
user = update.effective_user
user_id = str(user.id)
usuario = usuarios.setdefault(user_id, {})
usuario.setdefault("creditos", 0)
usuario.setdefault("consultas", 0)
usuario.setdefault("nombre", user.first_name or "Usuario")
usuario.setdefault("username", user.username or "")
usuario.setdefault("rol", "PENDIENTE")
usuario.setdefault("plan", "FREE")
usuario.setdefault("celular", "")
return user_id, usuario
#============================================================
#SISTEMA CENTRAL DE CRÉDITOS
#============================================================
async def validar_creditos(
user_id: str,
comando: str,
usuarios: Dict[str, Dict[str, Any]],
) -> Tuple[bool, Any]:
costo = PRECIOS.get(comando)
if costo is None:
return False, f"El servicio <code>/{html.escape(comando)}</code> no tiene precio configurado."
code
Code
saldo = int(usuarios.get(user_id, {}).get("creditos", 0) or 0)
if saldo < costo:
    return (
        False,
        "╔═════════════════════╗\n"
        "💳 <b>CRÉDITOS INSUFICIENTES</b>\n"
        "╚═════════════════════╝\n\n"
        f"❌ Saldo actual: <code>{saldo}</code> créditos\n"
        f"💎 Costo: <code>{costo}</code> créditos\n"
        f"📉 Faltan: <code>{costo - saldo}</code> créditos\n\n"
        "🛒 Usa <code>/buy</code> para recargar."
    )
return True, costo
async def cobrar_creditos(
user_id: str,
comando: str,
usuarios: Dict[str, Dict[str, Any]],
) -> int:
costo = int(PRECIOS[comando])
usuario = usuarios[user_id]
saldo = int(usuario.get("creditos", 0) or 0)
code
Code
if saldo < costo:
    raise ValueError("Saldo insuficiente al intentar cobrar la consulta.")

usuario["creditos"] = saldo - costo
usuario["consultas"] = int(usuario.get("consultas", 0) or 0) + 1
guardar_usuarios(usuarios)
return usuario["creditos"]
async def preparar_consulta(
update: Update,
comando: str,
usuarios: Dict[str, Dict[str, Any]],
user_id: str,
) -> Optional[int]:
ok, resultado = await validar_creditos(user_id, comando, usuarios)
if not ok:
await update.message.reply_text(
resultado,
parse_mode="HTML",
reply_markup=BTN_VOLVER,
)
return None
return int(resultado)
#============================================================
#CLIENTE API
#============================================================


async def consultar_api_get(url: str, timeout: float = 30.0) -> Dict[str, Any]:
headers = {
"Authorization": f"Bearer {API_TOKEN}",
"Accept": "application/json",
"Content-Type": "application/json",
}
try:
async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
response = await client.get(url, headers=headers)
if response.status_code == 401:
return {"error": "API_TOKEN inválido o expirado."}
response.raise_for_status()
try:
data = response.json()
except ValueError:
return {"error": "La API devolvió una respuesta que no es JSON."}
return data if isinstance(data, dict) else {"error": "Respuesta JSON inválida."}
except httpx.TimeoutException:
return {"error": "La API tardó demasiado en responder."}
except httpx.HTTPStatusError as exc:
return {"error": f"HTTP {exc.response.status_code}"}
except httpx.RequestError as exc:
return {"error": f"Error de conexión: {exc}"}
except Exception as exc:
logger.exception("Error API GET")
return {"error": str(exc)}
async def consultar_api_post_facial(imagen: bytes) -> Dict[str, Any]:
headers = {
"Authorization": f"Bearer {API_TOKEN}",
"Accept": "application/json",
}
files = {
"image_facial": ("imagen.jpg", imagen, "image/jpeg")
}
try:
async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
response = await client.post(
f"{BASE_URL}/api/v1/consultas/fd/facial/top",
headers=headers,
files=files,
)
if response.status_code != 200:
return {"error": f"API HTTP {response.status_code}: {response.text}"}
try:
data = response.json()
except ValueError:
return {"error": "La API facial devolvió una respuesta inválida."}
return data if isinstance(data, dict) else {"error": "Respuesta facial inválida."}
except httpx.TimeoutException:
return {"error": "La API facial tardó demasiado en responder."}
except httpx.RequestError as exc:
return {"error": f"Error de conexión: {exc}"}
except Exception as exc:
logger.exception("Error API facial")
return {"error": str(exc)}
async def notificar_usuario(user_id, monto, creditos, remitente):
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
mensaje = (
"✅ <b>PAGO DETECTADO</b>\n"
"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
f"• 💰 Recibido: <b>S/ {monto:.2f}</b>\n"
f"• 🎁 +<b>{creditos}</b> Créditos agregados ✅\n"
f"• 👤 De: {remitente}\n"
"┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
"⚡ ¡Ya puedes usar tus créditos!"
)
async with aiohttp.ClientSession() as session:
await session.post(url, json={
"chat_id": user_id,
"text": mensaje,
"parse_mode": "HTML"
})
#============================================================
#UTILIDADES DE RESPUESTA
#============================================================
async def responder_error(update: Update, mensaje: str) -> None:
await update.message.reply_text(
f"❌ <b>{html.escape(mensaje)}</b>",
parse_mode="HTML",
reply_markup=BTN_VOLVER,
)
async def editar_error(mensaje, mensaje_error: str) -> None:
await mensaje.edit_text(
f"❌ <b>{html.escape(mensaje_error)}</b>",
parse_mode="HTML",
reply_markup=BTN_VOLVER,
)
============================================================
COMANDOS DE CONSULTA IMPLEMENTADOS
============================================================
async def micelular(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
code
Code
if not context.args:
    return await update.message.reply_text(
        "📱 <b>Uso:</b> /micelular 987654321\n\n"
        "Guarda tu número de Yape para que los pagos\n"
        "se sumen automáticamente a tu saldo ⚡",
        parse_mode="HTML"
    )

celular = context.args[0].strip()
if not re.match(r"^9\d{8}$", celular):
    return await update.message.reply_text(
        "❌ Número inválido. Debe empezar con 9 y tener 9 dígitos.",
        parse_mode="HTML"
    )

usuario["celular"] = celular
guardar_usuarios(usuarios)
await update.message.reply_text(
    f"✅ <b>Número guardado:</b> {celular}\n\n"
    "💳 Ahora paga por Yape y los créditos\n"
    "se sumarán SOLOS en segundos ⚡",
    parse_mode="HTML"
)
async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
code
Code
if not usuario.get("celular"):
    return await update.message.reply_text(
        "⚠️ Primero guarda tu número:\n<code>/micelular 987654321</code>",
        parse_mode="HTML"
    )

monto = 5.0
if context.args:
    try:
        monto = max(1.0, float(context.args[0].replace(",", ".")))
    except:
        monto = 5.0

creditos = int(monto * TASA_CREDITOS)
qr_url = "https://files.catbox.moe/0y85js.jpg"

texto = (
    "💳 <b>INSTRUCCIONES DE PAGO</b>\n"
    "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
    f"• 💰 Monto: <b>S/ {monto:.2f}</b>\n"
    f"• 🎁 Recibes: <b>{creditos} Créditos</b>\n"
    f"• 📱 Paga al: <b>{TU_CELULAR_YAPE}</b>\n"
    f"• 👤 A nombre: <b>{TU_NOMBRE}</b>\n"
    "┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄\n"
    "✅ Abre Yape → Escanea el QR o paga al número\n"
    "⚡ Los créditos se suman SOLOS en segundos\n"
    "⚠️ NO envíes comprobante, el sistema lo detecta solo."
)

await update.message.reply_photo(
    photo=qr_url,
    caption=texto,
    parse_mode="HTML"
)
async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
saldo_actual = usuario.get("creditos", 0)
celular = usuario.get("celular", "No registrado")
code
Code
await update.message.reply_text(
    f"💰 <b>Tu Saldo:</b> {saldo_actual} Créditos\n"
    f"📱 Tu número: {celular}\n\n"
    "Usa /pagar para recargar más.",
    parse_mode="HTML"
)
async def dni(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
code
Code
if len(context.args) != 1:
    return await update.message.reply_text(
        f"{titulo_sistema('DNI • SISTEMA', '🪪')}\n\nUso: <code>/dni 12345678</code>\n💎 Costo: <code>{PRECIOS['dni']}</code> créditos",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )

dni_num = context.args[0].strip()
if not (dni_num.isdigit() and len(dni_num) == 8):
    return await responder_error(update, "El DNI debe contener exactamente 8 dígitos.")

costo = await preparar_consulta(update, "dni", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text(
    f"🔎 <b>CONSULTANDO DNI</b>\n🪪 DNI: <code>{dni_num}</code>\n💎 Costo: <code>{costo}</code> créditos\n\n⏳ Procesando...",
    parse_mode="HTML"
)

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/dni/{dni_num}")
    if data.get("error"): return await editar_error(mensaje, data["error"])
    if not data.get("success"): return await editar_error(mensaje, data.get("message", "No encontrado."))

    info = data.get("data", {})
    d = info.get("dni", {})
    n = info.get("nacimiento", {})
    dom = info.get("domicilio", {})
    gen = info.get("informacion_general", {})
    saldo_restante = await cobrar_creditos(user_id, "dni", usuarios)

    texto = (
        f"{titulo_sistema('DNI • RESULTADO', '🪪')}\n\n"
        f"🪪 <b>DNI:</b> <code>{error_html(d.get('completo', dni_num))}</code>\n"
        f"👤 <b>NOMBRE:</b> <code>{error_html(info.get('nombres'))} {error_html(info.get('apellidos'))}</code>\n"
        f"⚧️ <b>GÉNERO:</b> <code>{error_html(info.get('genero'))}</code>\n"
        f"📅 <b>NACIMIENTO:</b> <code>{error_html(n.get('fecha'))} ({error_html(n.get('edad'))})</code>\n"
        f"📍 <b>LUGAR:</b> <code>{error_html(n.get('distrito'))}, {error_html(n.get('provincia'))}</code>\n"
        f"🏠 <b>DIRECCIÓN:</b> <code>{error_html(dom.get('direccion'))}</code>\n"
        f"💍 <b>ESTADO CIVIL:</b> <code>{error_html(gen.get('estado_civil'))}</code>\n"
        f"👨 <b>PADRE:</b> <code>{error_html(gen.get('padre'))}</code>\n"
        f"👩 <b>MADRE:</b> <code>{error_html(gen.get('madre'))}</code>\n\n"
        f"{SEPARADOR}\n"
        f"💎 <b>COSTO:</b> <code>{costo}</code> crd\n"
        f"💳 <b>SALDO:</b> <code>{saldo_restante}</code> crd"
    )
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)

    images = info.get("images", [])
    if images:
        raw = base64.b64decode(images[0].get("data_uri").split(",")[1])
        await update.message.reply_photo(photo=BytesIO(raw), caption="📸 Foto RENIEC")
except Exception as e:
    logger.exception("Error en dni")
    await editar_error(mensaje, str(e))
async def dnit(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
code
Code
if len(context.args) != 1:
    return await update.message.reply_text(
        f"{titulo_sistema('DNI-T • SISTEMA', '💳')}\n\nUso: <code>/dnit 12345678</code>\n💎 Costo: <code>{PRECIOS['dnit']}</code> créditos",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )

dni_num = context.args[0].strip()
costo = await preparar_consulta(update, "dnit", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("🔎 Consultando DNI Completo (T)...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/dnit/{dni_num}")
    if not data.get("success"): return await editar_error(mensaje, data.get("message", "Error"))

    info = data.get("data", {})
    d = info.get("dni", {})
    n = info.get("nacimiento", {})
    gen = info.get("informacion_general", {})
    dom = info.get("domicilio", {})
    
    saldo_restante = await cobrar_creditos(user_id, "dnit", usuarios)

    texto = (
        f"{titulo_sistema('DNI-T • DETALLADO', '💳')}\n\n"
        f"🪪 <b>DNI:</b> <code>{error_html(d.get('completo'))}</code>\n"
        f"👤 <b>TITULAR:</b> <code>{error_html(info.get('nombres'))} {error_html(info.get('apellidos'))}</code>\n"
        f"🎂 <b>EDAD:</b> <code>{error_html(n.get('edad'))}</code>\n"
        f"📅 <b>FECHA NAC:</b> <code>{error_html(n.get('fecha'))}</code>\n"
        f"🎓 <b>ESTUDIOS:</b> <code>{error_html(gen.get('nivel_educativo'))}</code>\n"
        f"📏 <b>ESTATURA:</b> <code>{error_html(gen.get('estatura'))}</code>\n"
        f"📑 <b>EMISIÓN:</b> <code>{error_html(gen.get('fecha_emision'))}</code>\n"
        f"📅 <b>CADUCIDAD:</b> <code>{error_html(gen.get('fecha_caducidad'))}</code>\n"
        f"🏠 <b>DOMICILIO:</b> <code>{error_html(dom.get('direccion'))}</code>\n"
        f"📍 <b>UBICACIÓN:</b> <code>{error_html(dom.get('distrito'))} - {error_html(dom.get('provincia'))}</code>\n"
        f"{SEPARADOR}\n"
        f"💳 <b>SALDO:</b> <code>{saldo_restante}</code> crd"
    )
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)

    for img in info.get("images", [])[:2]:
        raw = base64.b64decode(img.get("data_uri").split(",")[1])
        await update.message.reply_photo(photo=BytesIO(raw))
except Exception as e:
    await editar_error(mensaje, str(e))
async def telpcel(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
code
Code
if len(context.args) != 1:
    return await update.message.reply_text(f"Uso: /telpcel 900000001", parse_mode="HTML")

numero = context.args[0].strip()
costo = await preparar_consulta(update, "telpcel", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("📡 Buscando titular de línea...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/telp/cel/{numero}")
    if not data.get("success"): return await editar_error(mensaje, "No se encontraron resultados.")

    res = data.get("data", {})
    titulares = res.get("titulares", [])
    saldo_restante = await cobrar_creditos(user_id, "telpcel", usuarios)

    texto = f"{titulo_sistema('TITULAR CELULAR', '📱')}\n\n"
    for t in titulares:
        texto += (
            f"👤 <b>TITULAR:</b> <code>{error_html(t.get('titular'))}</code>\n"
            f"🪪 <b>DNI/RUC:</b> <code>{error_html(t.get('dni_ruc'))}</code>\n"
            f"📡 <b>OPERADOR:</b> <code>{error_html(t.get('operador'))}</code>\n"
            f"💳 <b>PLAN:</b> <code>{error_html(t.get('plan'))}</code>\n"
            f"📧 <b>CORREO:</b> <code>{error_html(t.get('correo'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💳 <b>SALDO:</b> {saldo_restante} crd"
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
except Exception as e:
    await editar_error(mensaje, str(e))
async def telp(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /telp DNI")
code
Code
dni_num = context.args[0].strip()
costo = await preparar_consulta(update, "telp", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("🔎 Consultando líneas telefónicas...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/telp/{dni_num}")
    if not data.get("success"): return await editar_error(mensaje, "Sin líneas registradas.")

    res = data.get("data", {})
    lineas = res.get("lineas", [])
    saldo_restante = await cobrar_creditos(user_id, "telp", usuarios)

    texto = f"{titulo_sistema('LÍNEAS ASOCIADAS', '📡')}\n\n"
    for l in lineas:
        texto += (
            f"📱 <b>NÚMERO:</b> <code>{error_html(l.get('telefono'))}</code>\n"
            f"🏢 <b>OPERADOR:</b> <code>{error_html(l.get('operador'))}</code>\n"
            f"📅 <b>PERIODO:</b> <code>{error_html(l.get('periodo'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💳 <b>SALDO:</b> {saldo_restante} crd"
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
except Exception as e:
    await editar_error(mensaje, str(e))
async def agv(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /agv DNI")
code
Code
dni_num = context.args[0].strip()
costo = await preparar_consulta(update, "agv", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("🔎 Consultando AGV...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/agv/{dni_num}")
    if not data.get("success"): return await editar_error(mensaje, "No se encontró data.")

    res = data.get("data", {})
    saldo_restante = await cobrar_creditos(user_id, "agv", usuarios)

    texto = (
        f"{titulo_sistema('CONSULTA AGV', '🛰️')}\n\n"
        f"🪪 <b>DNI:</b> <code>{error_html(res.get('dni'))}</code>\n"
        f"👤 <b>NOMBRE:</b> <code>{error_html(res.get('nombres'))} {error_html(res.get('apellidos'))}</code>\n"
        f"⚧️ <b>GÉNERO:</b> <code>{error_html(res.get('genero'))}</code>\n"
        f"🎂 <b>EDAD:</b> <code>{error_html(res.get('edad'))}</code>\n\n"
        f"💳 <b>SALDO:</b> {saldo_restante} crd"
    )
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)

    if res.get("images"):
        raw = base64.b64decode(res["images"][0].get("data_uri").split(",")[1])
        await update.message.reply_photo(photo=BytesIO(raw))
except Exception as e:
    await editar_error(mensaje, str(e))
async def den(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /den DNI")
code
Code
dni_num = context.args[0].strip()
costo = await preparar_consulta(update, "denuncia", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("🔎 Buscando historial de denuncias...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/den/{dni_num}")
    if not data.get("success"): return await editar_error(mensaje, "Sin denuncias.")

    res = data.get("data", {})
    denuncias = res.get("denuncias", [])
    saldo_restante = await cobrar_creditos(user_id, "denuncia", usuarios)

    texto = f"{titulo_sistema('HISTORIAL DENUNCIAS', '🚨')}\n\n"
    for d in denuncias[:5]: # Mostrar las últimas 5 por espacio
        texto += (
            f"📌 <b>TIPO:</b> <code>{error_html(d.get('tipo'))}</code>\n"
            f"📅 <b>FECHA:</b> <code>{error_html(d.get('f_hecho'))}</code>\n"
            f"⚖️ <b>CONDICIÓN:</b> <code>{error_html(d.get('condicion'))}</code>\n"
            f"📄 <b>RESUMEN:</b> {error_html(d.get('resumen'))}\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💳 <b>SALDO:</b> {saldo_restante} crd"
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
except Exception as e:
    await editar_error(mensaje, str(e))
async def denuncias(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /denuncias DNI")
code
Code
dni_num = context.args[0].strip()
costo = await preparar_consulta(update, "denuncias", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("📂 Descargando archivos de denuncias...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/denuncias/{dni_num}")
    if not data.get("success"): return await editar_error(mensaje, "No se encontraron documentos.")

    res = data.get("data", {})
    archivos = res.get("denuncias", [])
    saldo_restante = await cobrar_creditos(user_id, "denuncias", usuarios)

    await mensaje.edit_text(f"✅ Se encontraron {len(archivos)} documentos. Enviando...", parse_mode="HTML")

    for doc in archivos:
        raw = base64.b64decode(doc.get("data_uri").split(",")[1])
        archivo = BytesIO(raw)
        archivo.name = doc.get("nombre", "denuncia.pdf")
        await update.message.reply_document(document=archivo, caption=f"🚨 Denuncia Tipo: {doc.get('tipo')}")
    
    await update.message.reply_text(f"💳 Saldo actual: {saldo_restante} crd")
except Exception as e:
    await editar_error(mensaje, str(e))
async def hsoat(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /hsoat PLACA")
code
Code
placa = context.args[0].strip().upper()
costo = await preparar_consulta(update, "hsoat", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("🚘 Consultando SOAT...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/hsoat/{placa}")
    if not data.get("success"): return await editar_error(mensaje, "Placa no encontrada en SOAT.")

    res = data.get("data", {})
    hist = res.get("historial", [])
    saldo_restante = await cobrar_creditos(user_id, "hsoat", usuarios)

    texto = f"{titulo_sistema('HISTORIAL SOAT', '🚗')}\n\n"
    for h in hist:
        texto += (
            f"🏢 <b>CIA:</b> <code>{error_html(h.get('compania'))}</code>\n"
            f"✅ <b>ESTADO:</b> <code>{error_html(h.get('estado'))}</code>\n"
            f"📅 <b>VENCE:</b> <code>{error_html(h.get('fecha_fin'))}</code>\n"
            f"📄 <b>PÓLIZA:</b> <code>{error_html(h.get('poliza'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💳 <b>SALDO:</b> {saldo_restante} crd"
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
except Exception as e:
    await editar_error(mensaje, str(e))
async def suel(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /suel DNI")
code
Code
dni_num = context.args[0].strip()
costo = await preparar_consulta(update, "suel", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("💰 Consultando ingresos y sueldos...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/suel/{dni_num}")
    if not data.get("success"): return await editar_error(mensaje, "Sin registros laborales.")

    res = data.get("data", {})
    sueldos = res.get("sueldos", [])
    saldo_restante = await cobrar_creditos(user_id, "suel", usuarios)

    texto = f"{titulo_sistema('REPORTE LABORAL', '💼')}\n\n"
    for s in sueldos:
        texto += (
            f"🏢 <b>EMPRESA:</b> <code>{error_html(s.get('empresa'))}</code>\n"
            f"📅 <b>PERIODO:</b> <code>{error_html(s.get('periodo'))}</code>\n"
            f"💰 <b>MONTO:</b> <code>{error_html(s.get('sueldo'))}</code>\n"
            f"👔 <b>ESTADO:</b> <code>{error_html(s.get('situacion'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💳 <b>SALDO:</b> {saldo_restante} crd"
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
except Exception as e:
    await editar_error(mensaje, str(e))
async def denpla(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /denpla PLACA")
code
Code
placa = context.args[0].strip().upper()
costo = await preparar_consulta(update, "denpla", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("🚨 Consultando denuncias vehiculares...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/denpla/{placa}")
    if not data.get("success"): return await editar_error(mensaje, "Sin denuncias para esta placa.")

    res = data.get("data", {})
    denuncias = res.get("denuncias", [])
    saldo_restante = await cobrar_creditos(user_id, "denpla", usuarios)

    texto = f"{titulo_sistema('DENUNCIAS PLACA', '🚨')}\n\n"
    for d in denuncias:
        texto += (
            f"📌 <b>NÚMERO:</b> <code>{error_html(d.get('numero'))}</code>\n"
            f"🏢 <b>COMISARÍA:</b> <code>{error_html(d.get('comisaria'))}</code>\n"
            f"📅 <b>FECHA:</b> <code>{error_html(d.get('f_hecho'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💳 <b>SALDO:</b> {saldo_restante} crd"
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
except Exception as e:
    await editar_error(mensaje, str(e))
async def facial(update: Update, context: ContextTypes.DEFAULT_TYPE):
message = update.message
if not message: return
code
Code
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)

if not message.photo:
    return await message.reply_text(
        f"{titulo_sistema('SISTEMA FACIAL', '🧬')}\n\n"
        "📷 Envía una foto con <code>/facial</code> en el caption.",
        parse_mode="HTML", reply_markup=BTN_VOLVER
    )

costo = await preparar_consulta(update, "facial", usuarios, user_id)
if costo is None: return

estado = await message.reply_text("🛰️ Escaneando rostro...", parse_mode="HTML")

try:
    photo = message.photo[-1]
    tg_file = await context.bot.get_file(photo.file_id)
    imagen = bytes(await tg_file.download_as_bytearray())
    data = await consultar_api_post_facial(imagen)

    if not data.get("success"): return await editar_error(estado, "No se encontraron coincidencias faciales.")

    info = data.get("data", {})
    rostros = info.get("rostros", [])
    saldo_restante = await cobrar_creditos(user_id, "facial", usuarios)

    texto = f"{titulo_sistema('MATCH FACIAL', '🧬')}\n\n"
    for r in rostros:
        for c in r.get("coincidencias", []):
            texto += (
                f"👤 <b>NOMBRE:</b> <code>{error_html(c.get('nombre'))}</code>\n"
                f"🪪 <b>DNI:</b> <code>{error_html(c.get('dni'))}</code>\n"
                f"🎯 <b>SIMILITUD:</b> <code>{error_html(c.get('porcentaje'))}%</code>\n"
                f"{SEPARADOR}\n"
            )
    texto += f"💳 <b>SALDO:</b> {saldo_restante} crd"
    await estado.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
except Exception as e:
    await editar_error(estado, str(e))

async def revtec(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /revtec PLACA")
code
Code
placa = context.args[0].strip().upper()
costo = await preparar_consulta(update, "revtec", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("🔍 Consultando Revisiones Técnicas...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/revtec/{placa}")
    if not data.get("success"): return await editar_error(mensaje, "Sin historial de revisiones.")

    res = data.get("data", {})
    regs = res.get("registros", [])
    saldo_restante = await cobrar_creditos(user_id, "revtec", usuarios)

    texto = f"{titulo_sistema('REVISIÓN TÉCNICA', '🛠️')}\n\n"
    for r in regs:
        texto += (
            f"✅ <b>ESTADO:</b> <code>{error_html(r.get('estado'))}</code>\n"
            f"🏢 <b>ENTIDAD:</b> <code>{error_html(r.get('entidad'))}</code>\n"
            f"📅 <b>VENCE:</b> <code>{error_html(r.get('fecha_vencimiento'))}</code>\n"
            f"📊 <b>RESULTADO:</b> <code>{error_html(r.get('resultado'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💳 <b>SALDO:</b> {saldo_restante} crd"
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
except Exception as e:
    await editar_error(mensaje, str(e))
async def dir_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /dir DNI")
code
Code
dni_num = context.args[0].strip()
costo = await preparar_consulta(update, "dir", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("🏠 Buscando historial de direcciones...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/dir/{dni_num}")
    if not data.get("success"): return await editar_error(mensaje, "Sin direcciones registradas.")

    res = data.get("data", {})
    direcciones = res.get("direcciones", [])
    saldo_restante = await cobrar_creditos(user_id, "dir", usuarios)

    texto = f"{titulo_sistema('HISTORIAL DIRECCIONES', '📍')}\n\n"
    for d in direcciones:
        texto += (
            f"🏠 <b>DIRECCIÓN:</b> <code>{error_html(d.get('direccion'))}</code>\n"
            f"📍 <b>UBICACIÓN:</b> <code>{error_html(d.get('ubicacion'))}</code>\n"
            f"📡 <b>FUENTE:</b> <code>{error_html(d.get('fuente'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💳 <b>SALDO:</b> {saldo_restante} crd"
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
except Exception as e:
    await editar_error(mensaje, str(e))
async def dnivel(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /dnivel DNI")
code
Code
dni_num = context.args[0].strip()
costo = await preparar_consulta(update, "dnivel", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("🔎 Consultando DNI-Nivel...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/dnivel/{dni_num}")
    if not data.get("success"): return await editar_error(mensaje, "No encontrado.")

    res = data.get("data", {})
    saldo_restante = await cobrar_creditos(user_id, "dnivel", usuarios)

    texto = (
        f"{titulo_sistema('DNI NIVEL', '📊')}\n\n"
        f"🪪 <b>DNI:</b> <code>{error_html(res.get('dni'))}</code>\n"
        f"👤 <b>NOMBRE:</b> <code>{error_html(res.get('nombres'))} {error_html(res.get('apellidos'))}</code>\n"
        f"🎂 <b>EDAD:</b> <code>{error_html(res.get('edad'))}</code>\n"
        f"⚧️ <b>GÉNERO:</b> <code>{error_html(res.get('genero'))}</code>\n\n"
        f"💳 <b>SALDO:</b> {saldo_restante} crd"
    )
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)

    if res.get("images"):
        for img in res["images"]:
            raw = base64.b64decode(img.get("data_uri").split(",")[1])
            await update.message.reply_photo(photo=BytesIO(raw))
except Exception as e:
    await editar_error(mensaje, str(e))
async def rqh(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
if len(context.args) != 1: return await responder_error(update, "Uso: /rqh DNI")
code
Code
dni_num = context.args[0].strip()
costo = await preparar_consulta(update, "rqh", usuarios, user_id)
if costo is None: return

mensaje = await update.message.reply_text("🚨 Consultando Requisitorias...", parse_mode="HTML")

try:
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/rqh/{dni_num}")
    if not data.get("success"): return await editar_error(mensaje, "Sin requisitorias registradas.")

    res = data.get("data", {})
    datos = res.get("datos_personales", {})
    resumen = res.get("resumen_requisitorias", {})
    saldo_restante = await cobrar_creditos(user_id, "rqh", usuarios)

    texto = (
        f"{titulo_sistema('REQUISITORIAS', '👮')}\n\n"
        f"👤 <b>NOMBRE:</b> <code>{error_html(datos.get('nombres'))}</code>\n"
        f"📊 <b>ESTADO:</b> {error_html(resumen.get('activas'))} ACTIVA(S)\n"
        f"📍 <b>DISTRITO:</b> <code>{error_html(datos.get('distrito'))}</code>\n\n"
    )
    for d in res.get("detalle", []):
        texto += (
            f"🔸 <b>ESTADO:</b> <code>{error_html(d.get('estado'))}</code>\n"
            f"⚖️ <b>DELITO:</b> <code>{error_html(d.get('delito'))}</code>\n"
            f"🏢 <b>JUZGADO:</b> <code>{error_html(d.get('dependencia'))}</code>\n"
            f"{SEPARADOR_CORTO}\n"
        )
    texto += f"💳 <b>SALDO:</b> {saldo_restante} crd"
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)

    for doc in res.get("documentos", []):
        raw = base64.b64decode(doc.get("data_uri").split(",")[1])
        archivo = BytesIO(raw)
        archivo.name = doc.get("nombre", "requisitoria.pdf")
        await update.message.reply_document(document=archivo)
except Exception as e:
    await editar_error(mensaje, str(e))
#============================================================
#COMANDOS GENERALES
#============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
texto = (
f"{titulo_sistema('SPECTER PERÚ', '⚜️')}\n\n"
"🚀 <b>PLATAFORMA DE CONSULTAS</b>\n\n"
f"🏷️ Nombre: <b>{html.escape(BOT_NAME)}</b>\n"
f"👤 Usuario: <b>{html.escape(BOT_USER)}</b>\n"
"🛰️ Estado: <b>ONLINE</b>\n\n"
f"{SEPARADOR}\n"
"📚 <b>COMANDOS PRINCIPALES</b>\n\n"
"📖 /cmds ➜ Ver servicios\n"
"👤 /me ➜ Ver perfil\n"
"💳 /buy ➜ Planes\n"
"💰 /saldo ➜ Tu crédito\n\n"
f"{SEPARADOR}\n"
"⚡ Sistema actualizado CODART X V1"
)
await update.message.reply_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
texto = (
f"{titulo_sistema('MENÚ DE SERVICIOS', '🛰️')}\n\n"
"💎 Selecciona una categoría abajo para ver los costos y comandos disponibles."
)
await update.message.reply_text(texto, parse_mode="HTML", reply_markup=menu_teclado())
async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
usuarios = cargar_usuarios()
user_id, usuario = obtener_usuario(update, usuarios)
guardar_usuarios(usuarios)
username = f"@{usuario.get('username')}" if usuario.get("username") else "Sin username"
code
Code
texto = (
    f"{titulo_sistema('PERFIL DE USUARIO', '👤')}\n\n"
    f"👤 Nombre: <code>{error_html(usuario.get('nombre', 'Usuario'))}</code>\n"
    f"🆔 ID: <code>{user_id}</code>\n"
    f"📱 Celular: <code>{error_html(usuario.get('celular'))}</code>\n"
    f"💳 Créditos: <code>{usuario.get('creditos', 0)}</code>\n"
    f"📊 Consultas: <code>{usuario.get('consultas', 0)}</code>\n"
    f"⭐ Plan: <code>{error_html(usuario.get('plan', 'FREE'))}</code>\n"
    f"{SEPARADOR}\n⚜️ <b>SPECTER PERÚ</b>"
)
await update.message.reply_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
texto = (
f"{titulo_sistema('PLANES PREMIUM', '💎')}\n\n"
"💰 <b>CRÉDITOS</b>\n"
"🥉 100 crd ➜ S/ 10\n"
"🥈 200 crd ➜ S/ 20\n"
"🥇 400 crd ➜ S/ 30\n\n"
"💳 <b>PAGOS:</b> Yape • Plin\n"
"👤 <b>ADMIN:</b> @Sthep_18\n\n"
"⚡ Usa /pagar para recarga automática."
)
await update.message.reply_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
texto = (
f"{titulo_sistema('STAFF OFICIAL', '👑')}\n\n"
"🛡️ <b>ADMINISTRADOR PRINCIPAL</b>\n"
"👤 @Sthep_18\n\n"
"🛠️ Soporte técnico y ventas."
)
await update.message.reply_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)
============================================================
ADMINISTRACIÓN
============================================================
async def addcreditos(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = str(update.effective_user.id)
if user_id not in ADMIN_ID: return
if len(context.args) != 2: return
target_id = context.args[0]
cantidad = int(context.args[1])
usuarios = cargar_usuarios()
if target_id not in usuarios: return
usuarios[target_id]["creditos"] = int(usuarios[target_id].get("creditos", 0)) + cantidad
guardar_usuarios(usuarios)
await update.message.reply_text(f"✅ Agregados {cantidad} a {target_id}")
async def quitarcrd(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = str(update.effective_user.id)
if user_id not in ADMIN_ID: return
if len(context.args) != 2: return
target_id = context.args[0]
cantidad = int(context.args[1])
usuarios = cargar_usuarios()
if target_id not in usuarios: return
usuarios[target_id]["creditos"] = max(0, int(usuarios[target_id].get("creditos", 0)) - cantidad)
guardar_usuarios(usuarios)
await update.message.reply_text(f"✅ Quitados {cantidad} a {target_id}")
#============================================================
#MENÚ INTERACTIVO CALLBACKS
#============================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
if not query: return
await query.answer()
code
Code
if query.data == "volver_cmds":
    return await query.edit_message_text(
        f"{titulo_sistema('MENÚ DE SERVICIOS', '🛰️')}\n\nSelecciona una categoría:",
        parse_mode="HTML", reply_markup=menu_teclado()
    )

textos = {
    "cmd_reniec": (
        f"{titulo_sistema('RENIEC', '🪪')}\n\n"
        f"/dni ➜ {PRECIOS['dni']} crd\n"
        f"/dnit ➜ {PRECIOS['dnit']} crd\n"
        f"/agv ➜ {PRECIOS['agv']} crd\n"
        f"/dnivel ➜ {PRECIOS['dnivel']} crd"
    ),
    "cmd_ruc": (
        f"{titulo_sistema('RUC', '🏢')}\n\n"
        f"/ruc ➜ {PRECIOS['ruc']} crd"
    ),
    "cmd_vehiculos": (
        f"{titulo_sistema('VEHÍCULOS', '🚘')}\n\n"
        f"/hsoat ➜ {PRECIOS['hsoat']} crd\n"
        f"/denpla ➜ {PRECIOS['denpla']} crd\n"
        f"/revtec ➜ {PRECIOS['revtec']} crd"
    ),
    "cmd_telefono": (
        f"{titulo_sistema('TELEFONÍA', '📱')}\n\n"
        f"/telp ➜ {PRECIOS['telp']} crd\n"
        f"/telpcel ➜ {PRECIOS['telpcel']} crd"
    ),
    "cmd_denuncia": (
        f"{titulo_sistema('DENUNCIAS', '⚖️')}\n\n"
        f"/den ➜ {PRECIOS['denuncia']} crd\n"
        f"/denuncias ➜ {PRECIOS['denuncias']} crd"
    ),
    "cmd_sueldo": (
        f"{titulo_sistema('SUELDOS', '💰')}\n\n"
        f"/suel ➜ {PRECIOS['suel']} crd"
    ),
    "cmd_facial": (
        f"{titulo_sistema('FACIAL', '🧬')}\n\n"
        f"/facial ➜ {PRECIOS['facial']} crd"
    ),
    "cmd_otros": (
        f"{titulo_sistema('OTROS', '🔍')}\n\n"
        f"/dir ➜ {PRECIOS['dir']} crd\n"
        f"/rqh ➜ {PRECIOS['rqh']} crd"
    ),
    "cmd_buy": "Usa /buy para información de pagos."
}

if query.data in textos:
    await query.edit_message_text(textos[query.data], parse_mode="HTML", reply_markup=BTN_VOLVER)


def main():
if not BOT_TOKEN: raise RuntimeError("Falta BOT_TOKEN")
keep_alive()
code
Code
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("cmds", cmds))
application.add_handler(CommandHandler("me", me))
application.add_handler(CommandHandler("buy", buy))
application.add_handler(CommandHandler("staff", staff))
application.add_handler(CommandHandler("saldo", saldo))
application.add_handler(CommandHandler("micelular", micelular))
application.add_handler(CommandHandler("pagar", pagar))
application.add_handler(CommandHandler("addcreditos", addcreditos))
application.add_handler(CommandHandler("quitarcrd", quitarcrd))

# Consultas
application.add_handler(CommandHandler("dni", dni))
application.add_handler(CommandHandler("dnit", dnit))
application.add_handler(CommandHandler("agv", agv))
application.add_handler(CommandHandler("den", den))
application.add_handler(CommandHandler("denuncias", denuncias))
application.add_handler(CommandHandler("telp", telp))
application.add_handler(CommandHandler("telpcel", telpcel))
application.add_handler(CommandHandler("hsoat", hsoat))
application.add_handler(CommandHandler("suel", suel))
application.add_handler(CommandHandler("denpla", denpla))
application.add_handler(CommandHandler("revtec", revtec))
application.add_handler(CommandHandler("dir", dir_cmd))
application.add_handler(CommandHandler("dnivel", dnivel))
application.add_handler(CommandHandler("rqh", rqh))
application.add_handler(CommandHandler("facial", facial))

application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.PHOTO & filters.CaptionRegex(r"^/facial(?:\s|$)"), facial))

logger.info("🚀 SPECTER PERÚ ONLINE")
application.run_polling(drop_pending_updates=True)
if __name__ == "__main__":
    main()