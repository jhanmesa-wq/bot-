import asyncio
import base64
import datetime
import html
import io
import json
import logging
import os
from io import BytesIO
from threading import Thread
from typing import Any, Dict, Optional, Tuple

import httpx
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("specter_peru")

# ============================================================
# CONFIGURACIÓN
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_TOKEN = os.getenv("API_TOKEN")
ARCHIVO_USUARIOS = os.getenv("ARCHIVO_USUARIOS") or "usuarios.json"
BASE_URL = os.getenv("BASE_URL") or "https://api-codart.cgrt.org"
BOT_USER = "@specter_Dox44bot"
BOT_NAME = "⚜ SPECTER PERÚ ⚜"
CLAVE_SECRETA = os.getenv("CLAVE_SECRETA", "PON_TU_CLAVE_AQUI")  # MISMA QUE EN TU APK
TASA_CREDITOS = 1
TU_CELULAR_YAPE = "925805734"
TU_NOMBRE = "CHRISTIAN GUSTAVO RAMOS GONZALES"
# Permite varios administradores separados por coma.
ADMIN_ID = {
    item.strip()
    for item in (os.getenv("ADMIN_ID") or "").split(",")
    if item.strip()
}

# Precios de los servicios que ya existen en el código original.
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
}

# ============================================================
# FLASK KEEP-ALIVE
# ============================================================
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

app_flask = Flask('')

@app_flask.route('/')
def home():
    return "🔥 SPECTER PERÚ BOT ACTIVO 24/7"

@app_flask.route('/health')
def health():
    return "OK", 200

def run_flask():
    # Render asigna un puerto automáticamente en la variable de entorno PORT
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# ============================================================
# ESTILO FUTURISTA CENTRALIZADO
# ============================================================
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
                InlineKeyboardButton("💎 COMPRAR", callback_data="cmd_buy"),
            ],
        ]
    )


def titulo_sistema(nombre: str, icono: str = "⚡") -> str:
    return (
        f"╔═════════════════════╗\n"
        f"{icono} <b>{html.escape(nombre.upper())}</b>\n"
        f"╚═════════════════════╝"
    )


def error_html(texto: Any) -> str:
    return html.escape(str(texto))


# ============================================================
# BASE DE DATOS DE USUARIOS
# ============================================================
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
    return user_id, usuario


# ============================================================
# SISTEMA CENTRAL DE CRÉDITOS
# ============================================================
async def validar_creditos(
    user_id: str,
    comando: str,
    usuarios: Dict[str, Dict[str, Any]],
) -> Tuple[bool, Any]:
    costo = PRECIOS.get(comando)
    if costo is None:
        return False, f"El servicio <code>/{html.escape(comando)}</code> no tiene precio configurado."

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
    """Descuenta créditos únicamente después de confirmar una consulta exitosa."""
    costo = int(PRECIOS[comando])
    usuario = usuarios[user_id]
    saldo = int(usuario.get("creditos", 0) or 0)

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


# ============================================================
# CLIENTE API
# ============================================================
async def consultar_api_get(url: str, timeout: float = 30.0) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
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


# ============================================================
# UTILIDADES DE VALIDACIÓN / RESPUESTA
# ============================================================
def argumento_unico(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    uso: str,
) -> Optional[str]:
    if len(context.args) != 1:
        return None
    return context.args[0].strip()


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


# ============================================================
# COMANDOS DE CONSULTA
# ============================================================

# ═══ BASE DE DATOS ═══
ARCHIVO_USUARIOS = "usuarios2.json"

def cargar_usuarios():
    try:
        with open(ARCHIVO_USUARIOS, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def guardar_usuarios(usuarios):
    with open(ARCHIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)

# ═══ COMANDOS DEL BOT ═══

async def micelular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios()
    usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})

    if not context.args:
        return await update.message.reply_text(
            "📱 <b>Uso:</b> /micelular 987654321\n\n"
            "Guarda tu número de Yape para que los pagos\n"
            "se sumen automáticamente a tu saldo ⚡",
            parse_mode="HTML"
        )

    celular = context.args[0].strip()
    if not re.match(r"^9\\d{8}$", celular):
        return await update.message.reply_text(
            "❌ Número inválido. Debe empezar con 9 y tener 8 dígitos.",
            parse_mode="HTML"
        )

    usuarios[user_id]["celular"] = celular
    guardar_usuarios(usuarios)
    await update.message.reply_text(
        f"✅ <b>Número guardado:</b> {celular}\n\n"
        "💳 Ahora paga por Yape y los créditos\n"
        "se sumarán SOLOS en segundos ⚡",
        parse_mode="HTML"
    )

async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios()
    usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})

    if not usuarios[user_id].get("celular"):
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
    qr_url = f"https://files.catbox.moe/0y85js.jpg:{TU_CELULAR_YAPE}?amount={monto}"

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
        "⚠️ NO envíes comprobante, el sistema lo detecta solo.",
        parse_mode="HTML"
    )
    await update.message.reply_photo(photo=qr_url, caption=texto)

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    usuarios = cargar_usuarios()
    usuarios.setdefault(user_id, {"creditos": 0, "consultas": 0})
    saldo_actual = usuarios[user_id].get("creditos", 0)
    celular = usuarios[user_id].get("celular", "No registrado")

    await update.message.reply_text(
        f"💰 <b>Tu Saldo:</b> {saldo_actual} Créditos\n"
        f"📱 Tu número: {celular}\n\n"
        "Usa /pagar para recargar más.",
        parse_mode="HTML"
    )

# ═══ FUNCIÓN QUE LLAMA TU APK PARA SUMAR CRÉDITOS ═══
@app.route("/webhook-pagos/", methods=["POST"])
def recibir_pago():
    # 📥 Recibir datos SIN pedir clave
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "Sin datos"}), 400

    celular = datos.get("numero", "").strip()
    monto_str = datos.get("monto", "0")
    remitente = datos.get("de", "Desconocido")

    try:
        monto = float(monto_str.replace(",", "."))
    except:
        return jsonify({"error": "Monto inválido"}), 400

    creditos = int(monto * TASA_CREDITOS)

    # 🔍 Buscar usuario por su celular
    usuarios = cargar_usuarios()
    user_id_encontrado = None
    for user_id, info in usuarios.items():
        if str(info.get("celular", "")).strip() == celular:
            user_id_encontrado = user_id
            break

    # ✅ SUMAR CRÉDITOS
    if user_id_encontrado and creditos > 0:
        usuarios[user_id_encontrado]["creditos"] = usuarios[user_id_encontrado].get("creditos", 0) + creditos
        guardar_usuarios(usuarios)
        print(f"✅ PAGO — S/{monto} de {remitente} → +{creditos} créditos a {user_id_encontrado}")
    else:
        print(f"⚠️ Pago S/{monto} de {remitente} — Usuario NO REGISTRADO: {celular}")

    return jsonify({"status": "ok"}), 200
# ═══ NOTIFICAR AL USUARIO ═══
async def notificar_usuario(user_id, monto, creditos, remitente):
    """Avisar al usuario que se le sumaron los créditos"""
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

async def agv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

    if len(context.args) != 1:
        return await update.message.reply_text(
            "╔═════════════════════╗\n"
            "🛰️ <b>CONSULTA AGV</b>\n"
            "╚═════════════════════╝\n\n"
            "Uso: <code>/agv 12345678</code>",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    dni = context.args[0].strip()
    if not (dni.isdigit() and len(dni) == 8):
        return await responder_error(update, "El DNI debe contener exactamente 8 dígitos.")

    costo = await preparar_consulta(update, "agv", usuarios, user_id)
    if costo is None:
        return

    mensaje = await update.message.reply_text(
        f"🔎 <b>CONSULTANDO AGV</b>\n\n🪪 DNI: <code>{html.escape(dni)}</code>\n💎 Costo: <code>{costo}</code> créditos\n\n⏳ Procesando...",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )

    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/agv/{dni}")
    if data.get("error"):
        return await editar_error(mensaje, data["error"])
    if not data.get("success"):
        return await editar_error(mensaje, data.get("message", "No se encontró información."))

    info = data.get("data") or {}
    if not isinstance(info, dict):
        return await editar_error(mensaje, "La API devolvió datos inválidos.")

    saldo = await cobrar_creditos(user_id, "agv", usuarios)

    texto = (
        f"{titulo_sistema('CONSULTA AGV', '🛰️')}\n\n"
        f"🟢 <b>ESTADO</b> ➜ ONLINE\n\n"
        f"🪪 <b>DNI:</b> <code>{error_html(info.get('dni', dni))}</code>\n"
        f"👤 <b>NOMBRE:</b> <code>{error_html(info.get('nombres', '-'))} {error_html(info.get('apellidos', '-'))}</code>\n"
        f"⚧️ <b>GÉNERO:</b> <code>{error_html(info.get('genero', '-'))}</code>\n"
        f"🎂 <b>EDAD:</b> <code>{error_html(info.get('edad', '-'))}</code>\n\n"
        f"{SEPARADOR}\n"
        f"💎 <b>DESCUENTO:</b> <code>{costo}</code> créditos\n"
        f"💳 <b>SALDO:</b> <code>{saldo}</code> créditos\n"
        f"⚜️ <b>SPECTER PERÚ</b>"
    )
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)

    images = info.get("images") or []
    if images and isinstance(images, list):
        for image_info in images[:3]:
            try:
                data_uri = image_info.get("data_uri", "")
                if "," not in data_uri:
                    continue
                raw = base64.b64decode(data_uri.split(",", 1)[1])
                await update.message.reply_photo(
                    photo=BytesIO(raw),
                    caption="📸 <b>Imagen asociada</b>",
                    parse_mode="HTML",
                    reply_markup=BTN_VOLVER,
                )
            except Exception:
                logger.exception("No se pudo enviar imagen AGV")


async def den(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

    if len(context.args) != 1:
        return await update.message.reply_text(
            "╔═════════════════════╗\n🚨 <b>DENUNCIAS POR DNI</b>\n╚═════════════════════╝\n\nUso: <code>/den 12345678</code>",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    dni = context.args[0].strip()
    if not (dni.isdigit() and len(dni) == 8):
        return await responder_error(update, "El DNI debe contener exactamente 8 dígitos.")

    costo = await preparar_consulta(update, "denuncia", usuarios, user_id)
    if costo is None:
        return

    mensaje = await update.message.reply_text(
        f"🔎 <b>CONSULTANDO DENUNCIAS</b>\n🪪 DNI: <code>{dni}</code>\n💎 Costo: <code>{costo}</code> créditos",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )

    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/den/{dni}")
    if data.get("error"):
        return await editar_error(mensaje, data["error"])
    if not data.get("success"):
        return await editar_error(mensaje, data.get("message", "No se encontraron denuncias."))

    info = data.get("data") or {}
    if not isinstance(info, dict):
        return await editar_error(mensaje, "La API devolvió datos inválidos.")

    saldo = await cobrar_creditos(user_id, "denuncia", usuarios)
    denuncias = info.get("denuncias") or []

    texto = (
        f"{titulo_sistema('CONSULTA DE DENUNCIAS', '🚨')}\n\n"
        f"🪪 <b>DNI:</b> <code>{error_html(info.get('consulta', dni))}</code>\n"
        f"📊 <b>TOTAL:</b> <code>{error_html(info.get('cantidad_denuncias', len(denuncias)))}</code>\n\n"
    )
    for i, item in enumerate(denuncias, 1):
        texto += (
            f"📌 <b>DENUNCIA #{i}</b>\n"
            f"• Tipo: <code>{error_html(item.get('tipo', '-'))}</code>\n"
            f"• Orden: <code>{error_html(item.get('n_orden', '-'))}</code>\n"
            f"• Fecha: <code>{error_html(item.get('f_hecho', '-'))}</code>\n"
            f"• Condición: <code>{error_html(item.get('condicion', '-'))}</code>\n"
            f"• Resumen: <code>{error_html(item.get('resumen', '-'))}</code>\n"
            f"{SEPARADOR}\n"
        )

    texto += f"💎 <b>DESCUENTO:</b> <code>{costo}</code> créditos\n💳 <b>SALDO:</b> <code>{saldo}</code> créditos\n⚜️ <b>SPECTER PERÚ</b>"
    await mensaje.edit_text(texto[:4090], parse_mode="HTML", reply_markup=BTN_VOLVER)


async def denuncias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

    if len(context.args) != 1:
        return await update.message.reply_text(
            "╔═════════════════════╗\n📂 <b>DENUNCIAS EN PDF</b>\n╚═════════════════════╝\n\nUso: <code>/denuncias 12345678</code>",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    dni = context.args[0].strip()
    if not (dni.isdigit() and len(dni) == 8):
        return await responder_error(update, "El DNI debe contener exactamente 8 dígitos.")

    # El menú original mostraba 30 créditos para este servicio.
    precio = 30
    PRECIOS.setdefault("denuncias", precio)

    ok, resultado = await validar_creditos(user_id, "denuncias", usuarios)
    if not ok:
        return await update.message.reply_text(resultado, parse_mode="HTML", reply_markup=BTN_VOLVER)

    mensaje = await update.message.reply_text(
        f"🔎 <b>CONSULTANDO DENUNCIAS PDF</b>\n🪪 DNI: <code>{dni}</code>\n💎 Costo: <code>{precio}</code> créditos",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )

    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/denuncias/{dni}")
    if data.get("error"):
        return await editar_error(mensaje, data["error"])
    if not data.get("success"):
        return await editar_error(mensaje, data.get("message", "No se encontraron denuncias."))

    info = data.get("data") or {}
    lista = info.get("denuncias") or []
    if not lista:
        return await editar_error(mensaje, "No se encontraron archivos de denuncias.")

    saldo = await cobrar_creditos(user_id, "denuncias", usuarios)
    await mensaje.edit_text(
        f"{titulo_sistema('DENUNCIAS PDF', '📂')}\n\n"
        f"📊 Archivos encontrados: <code>{len(lista)}</code>\n"
        f"💎 Descuento: <code>{precio}</code> créditos\n"
        f"💳 Saldo: <code>{saldo}</code> créditos\n\n"
        "📤 Enviando documentos...",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )

    for den_data in lista:
        try:
            data_uri = den_data.get("data_uri", "")
            if "," not in data_uri:
                continue
            raw = base64.b64decode(data_uri.split(",", 1)[1])
            archivo = BytesIO(raw)
            nombre = den_data.get("nombre") or f"denuncia_{den_data.get('numero', 'archivo')}.pdf"
            archivo.name = nombre
            caption = (
                f"🚨 <b>DENUNCIA #{error_html(den_data.get('numero', '-'))}</b>\n"
                f"📌 Tipo: <code>{error_html(den_data.get('tipo', '-'))}</code>\n"
                f"🏢 Comisaría: <code>{error_html(den_data.get('comisaria', '-'))}</code>\n"
                f"📄 Orden: <code>{error_html(den_data.get('n_orden', '-'))}</code>"
            )
            await update.message.reply_document(
                document=archivo,
                filename=nombre,
                caption=caption,
                parse_mode="HTML",
                reply_markup=BTN_VOLVER,
            )
        except Exception:
            logger.exception("No se pudo enviar PDF de denuncia")


async def facial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

    # La foto puede venir como /facial en el caption.
    if not message.photo:
        return await message.reply_text(
            f"{titulo_sistema('SISTEMA FACIAL', '🧬')}\n\n"
            "📷 Envía una fotografía con el comando <code>/facial</code> en la descripción.\n\n"
            f"💎 Costo: <code>{PRECIOS['facial']}</code> créditos",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    costo = await preparar_consulta(update, "facial", usuarios, user_id)
    if costo is None:
        return

    estado = await message.reply_text(
        f"{titulo_sistema('ESCÁNER FACIAL', '🧬')}\n\n"
        "🛰️ Conectando al servidor...\n"
        "📷 Procesando imagen...\n"
        "🔎 Analizando solicitud...",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )

    try:
        photo = message.photo[-1]
        tg_file = await context.bot.get_file(photo.file_id)
        imagen = bytes(await tg_file.download_as_bytearray())
        data = await consultar_api_post_facial(imagen)

        if data.get("error"):
            return await editar_error(estado, data["error"])
        if not data.get("success"):
            return await editar_error(estado, data.get("message", "No se encontraron coincidencias."))

        info = data.get("data") or {}
        saldo = await cobrar_creditos(user_id, "facial", usuarios)

        texto = (
            f"{titulo_sistema('RESULTADO FACIAL', '🧬')}\n\n"
            f"🟢 <b>ESTADO:</b> CONSULTA COMPLETADA\n"
            f"🔎 <b>TIPO:</b> <code>{error_html(info.get('tipo_resultado', '-'))}</code>\n"
            f"👥 <b>COINCIDENCIAS:</b> <code>{error_html(info.get('coincidencias_mostradas', '-'))}</code>\n\n"
        )
        for i, persona in enumerate(info.get("coincidencias", []) or [], 1):
            texto += (
                f"👤 <b>COINCIDENCIA #{i}</b>\n"
                f"🪪 DNI: <code>{error_html(persona.get('dni', '-'))}</code>\n"
                f"📛 Nombre: <code>{error_html(persona.get('nombre', '-'))}</code>\n"
                f"🎯 Similitud: <code>{error_html(persona.get('porcentaje', '-'))}%</code>\n"
                f"{SEPARADOR}\n"
            )
        texto += f"💎 <b>DESCUENTO:</b> <code>{costo}</code> créditos\n💳 <b>SALDO:</b> <code>{saldo}</code> créditos\n⚜️ <b>SPECTER PERÚ</b>"
        await estado.edit_text(texto[:4090], parse_mode="HTML", reply_markup=BTN_VOLVER)
    except Exception as exc:
        logger.exception("Error en facial")
        await editar_error(estado, str(exc))


async def telpcel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

    if len(context.args) != 1:
        return await update.message.reply_text(
            f"{titulo_sistema('TELP CEL', '📱')}\n\nUso: <code>/telpcel 900000001</code>\n💎 Costo: <code>{PRECIOS['telpcel']}</code> créditos",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    numero = context.args[0].strip()
    if not (numero.isdigit() and len(numero) == 9):
        return await responder_error(update, "El número debe contener exactamente 9 dígitos.")

    costo = await preparar_consulta(update, "telpcel", usuarios, user_id)
    if costo is None:
        return

    mensaje = await update.message.reply_text(
        f"📡 <b>CONSULTANDO TELP CEL</b>\n📱 Número: <code>{numero}</code>\n💎 Costo: <code>{costo}</code> créditos",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/telp/cel/{numero}")
    if data.get("error"):
        return await editar_error(mensaje, data["error"])
    if not data.get("success"):
        return await editar_error(mensaje, data.get("message", "No se encontraron resultados."))

    titulares = (data.get("data") or {}).get("titulares") or []
    saldo = await cobrar_creditos(user_id, "telpcel", usuarios)

    texto = f"{titulo_sistema('TELP CEL • RESULTADO', '📱')}\n\n"
    for i, item in enumerate(titulares, 1):
        texto += (
            f"👤 <b>TITULAR #{i}</b>\n"
            f"📱 Teléfono: <code>{error_html(item.get('telefono', '-'))}</code>\n"
            f"🏢 Operador: <code>{error_html(item.get('operador', '-'))}</code>\n"
            f"🪪 DNI/RUC: <code>{error_html(item.get('dni_ruc', '-'))}</code>\n"
            f"💳 Plan: <code>{error_html(item.get('plan', '-'))}</code>\n"
            f"📧 Correo: <code>{error_html(item.get('correo', '-'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💎 <b>DESCUENTO:</b> <code>{costo}</code> créditos\n💳 <b>SALDO:</b> <code>{saldo}</code> créditos\n⚜️ <b>SPECTER PERÚ</b>"
    await mensaje.edit_text(texto[:4090], parse_mode="HTML", reply_markup=BTN_VOLVER)


async def telp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

    if len(context.args) != 1:
        return await update.message.reply_text(
            f"{titulo_sistema('TELP', '📡')}\n\nUso: <code>/telp 12345678</code>\n💎 Costo: <code>{PRECIOS['telp']}</code> créditos",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    dni = context.args[0].strip()
    if not (dni.isdigit() and len(dni) == 8):
        return await responder_error(update, "El DNI debe contener exactamente 8 dígitos.")

    costo = await preparar_consulta(update, "telp", usuarios, user_id)
    if costo is None:
        return

    mensaje = await update.message.reply_text(
        f"📡 <b>CONSULTANDO LÍNEAS</b>\n🪪 DNI: <code>{dni}</code>\n💎 Costo: <code>{costo}</code> créditos",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/telp/{dni}")
    if data.get("error"):
        return await editar_error(mensaje, data["error"])
    if not data.get("success"):
        return await editar_error(mensaje, data.get("message", "No se encontraron líneas telefónicas."))

    resultado = data.get("data") or {}
    lineas = resultado.get("lineas") or []
    saldo = await cobrar_creditos(user_id, "telp", usuarios)

    texto = (
        f"{titulo_sistema('TELP • RESULTADO', '📡')}\n\n"
        f"🪪 DNI: <code>{dni}</code>\n"
        f"📞 Líneas encontradas: <code>{resultado.get('lineas_encontradas', len(lineas))}</code>\n\n"
    )
    for i, linea in enumerate(lineas, 1):
        periodo = str(linea.get("periodo", "-"))
        if len(periodo) == 6 and periodo.isdigit():
            periodo = f"{periodo[4:]}/{periodo[:4]}"
        texto += (
            f"📱 <b>LÍNEA #{i}</b>\n"
            f"☎️ Número: <code>{error_html(linea.get('telefono', '-'))}</code>\n"
            f"📡 Operador: <code>{error_html(linea.get('operador', '-'))}</code>\n"
            f"🏢 Empresa: <code>{error_html(linea.get('empresa', '-'))}</code>\n"
            f"📅 Periodo: <code>{error_html(periodo)}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💎 <b>DESCUENTO:</b> <code>{costo}</code> créditos\n💳 <b>SALDO:</b> <code>{saldo}</code> créditos\n⚜️ <b>SPECTER PERÚ</b>"
    await mensaje.edit_text(texto[:4090], parse_mode="HTML", reply_markup=BTN_VOLVER)


async def dni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

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
    if costo is None:
        return

    mensaje = await update.message.reply_text(
        f"🔎 <b>CONSULTANDO DNI</b>\n🪪 DNI: <code>{dni_num}</code>\n💎 Costo: <code>{costo}</code> créditos\n\n⏳ Procesando...",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/dni/{dni_num}", timeout=15)
    if data.get("error"):
        return await editar_error(mensaje, data["error"])
    if not data.get("success"):
        return await editar_error(mensaje, data.get("message", "DNI no encontrado."))

    res = data.get("data") or {}
    if not isinstance(res, dict):
        return await editar_error(mensaje, "La API devolvió datos inválidos.")

    saldo = await cobrar_creditos(user_id, "dni", usuarios)
    d = res.get("dni") if isinstance(res.get("dni"), dict) else {}
    n = res.get("nacimiento") if isinstance(res.get("nacimiento"), dict) else {}
    dom = res.get("domicilio") if isinstance(res.get("domicilio"), dict) else {}
    info = res.get("informacion_general") if isinstance(res.get("informacion_general"), dict) else {}

    texto = (
        f"{titulo_sistema('DNI • RESULTADO', '🪪')}\n\n"
        f"🟢 <b>ESTADO:</b> ONLINE\n\n"
        f"🪪 <b>DNI:</b> <code>{error_html(d.get('completo', dni_num))}</code>\n"
        f"👤 <b>TITULAR:</b> <code>{error_html(res.get('nombres', '-'))} {error_html(res.get('apellidos', '-'))}</code>\n"
        f"⚧️ <b>GÉNERO:</b> <code>{error_html(res.get('genero', '-'))}</code>\n"
        f"📅 <b>NACIMIENTO:</b> <code>{error_html(n.get('fecha', '-'))} | {error_html(n.get('edad', '-'))}</code>\n"
        f"🏠 <b>DOMICILIO:</b> <code>{error_html(dom.get('direccion', '-'))} - {error_html(dom.get('distrito', '-'))}</code>\n"
        f"👨 <b>PADRE:</b> <code>{error_html(info.get('padre', '-'))}</code>\n"
        f"👩 <b>MADRE:</b> <code>{error_html(info.get('madre', '-'))}</code>\n\n"
        f"{SEPARADOR}\n"
        f"💎 <b>DESCUENTO:</b> <code>{costo}</code> créditos\n"
        f"💳 <b>SALDO:</b> <code>{saldo}</code> créditos\n"
        f"⚜️ <b>SPECTER PERÚ</b>\n"
        f"📡 Powered by CODART X API V1"
    )
    await mensaje.edit_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)


async def dnit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

    if len(context.args) != 1:
        return await update.message.reply_text(
            f"{titulo_sistema('DNI-T • SISTEMA', '💳')}\n\nUso: <code>/dnit 12345678</code>\n💎 Costo: <code>{PRECIOS['dnit']}</code> créditos",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    dni_num = context.args[0].strip()
    if not (dni_num.isdigit() and len(dni_num) == 8):
        return await responder_error(update, "El DNI debe contener exactamente 8 dígitos.")

    costo = await preparar_consulta(update, "dnit", usuarios, user_id)
    if costo is None:
        return

    mensaje = await update.message.reply_text(
        f"🔎 <b>CONSULTANDO DNI-T</b>\n🪪 DNI: <code>{dni_num}</code>\n💎 Costo: <code>{costo}</code> créditos",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/dnit/{dni_num}")
    if data.get("error"):
        return await editar_error(mensaje, data["error"])
    if not data.get("success"):
        return await editar_error(mensaje, data.get("message", "No se encontraron resultados."))

    res = data.get("data") or {}
    saldo = await cobrar_creditos(user_id, "dnit", usuarios)
    d = res.get("dni") if isinstance(res.get("dni"), dict) else {}
    n = res.get("nacimiento") if isinstance(res.get("nacimiento"), dict) else {}
    dom = res.get("domicilio") if isinstance(res.get("domicilio"), dict) else {}
    info = res.get("informacion_general") if isinstance(res.get("informacion_general"), dict) else {}

    texto = (
        f"{titulo_sistema('DNI-T • RESULTADO', '💳')}\n\n"
        f"🪪 DNI: <code>{error_html(d.get('completo', dni_num))}</code>\n"
        f"👤 Titular: <code>{error_html(res.get('nombres', '-'))} {error_html(res.get('apellidos', '-'))}</code>\n"
        f"⚧️ Género: <code>{error_html(res.get('genero', '-'))}</code>\n"
        f"📅 Nacimiento: <code>{error_html(n.get('fecha', '-'))} | {error_html(n.get('edad', '-'))}</code>\n"
        f"📍 Lugar: <code>{error_html(n.get('distrito', '-'))}, {error_html(n.get('provincia', '-'))}, {error_html(n.get('departamento', '-'))}</code>\n"
        f"🏠 Domicilio: <code>{error_html(dom.get('direccion', '-'))}</code>\n"
        f"🎓 Nivel educativo: <code>{error_html(info.get('nivel_educativo', '-'))}</code>\n"
        f"💍 Estado civil: <code>{error_html(info.get('estado_civil', '-'))}</code>\n"
        f"📏 Estatura: <code>{error_html(info.get('estatura', '-'))}</code>\n"
        f"📅 Inscripción: <code>{error_html(info.get('fecha_inscripcion', '-'))}</code>\n"
        f"📅 Emisión: <code>{error_html(info.get('fecha_emision', '-'))}</code>\n"
        f"📅 Caducidad: <code>{error_html(info.get('fecha_caducidad', '-'))}</code>\n"
        f"👨 Padre: <code>{error_html(info.get('padre', '-'))}</code>\n"
        f"👩 Madre: <code>{error_html(info.get('madre', '-'))}</code>\n\n"
        f"{SEPARADOR}\n💎 <b>DESCUENTO:</b> <code>{costo}</code> créditos\n💳 <b>SALDO:</b> <code>{saldo}</code> créditos\n⚜️ <b>SPECTER PERÚ</b>"
    )
    await mensaje.edit_text(texto[:4090], parse_mode="HTML", reply_markup=BTN_VOLVER)

    images = res.get("images") or []
    for i, image_info in enumerate(images[:3], 1):
        try:
            data_uri = image_info.get("data_uri", "")
            if "," not in data_uri:
                continue
            raw = base64.b64decode(data_uri.split(",", 1)[1])
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(raw),
                caption=f"📸 <b>Imagen {i} del documento</b>",
                parse_mode="HTML",
                reply_markup=BTN_VOLVER,
            )
        except Exception:
            logger.exception("No se pudo enviar imagen DNI-T")


async def hsoat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

    if len(context.args) != 1:
        return await update.message.reply_text(
            f"{titulo_sistema('HSOAT', '🚗')}\n\nUso: <code>/hsoat ABC123</code>\n💎 Costo: <code>{PRECIOS['hsoat']}</code> créditos",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    placa = context.args[0].strip().upper()
    if not (3 <= len(placa) <= 8 and placa.isalnum()):
        return await responder_error(update, "La placa debe contener entre 3 y 8 caracteres alfanuméricos.")

    costo = await preparar_consulta(update, "hsoat", usuarios, user_id)
    if costo is None:
        return

    mensaje = await update.message.reply_text(
        f"🔎 <b>CONSULTANDO HSOAT</b>\n🚗 Placa: <code>{placa}</code>\n💎 Costo: <code>{costo}</code> créditos",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/hsoat/{placa}")
    if data.get("error"):
        return await editar_error(mensaje, data["error"])
    if not data.get("success"):
        return await editar_error(mensaje, data.get("message", "Placa no encontrada."))

    res = data.get("data") or {}
    saldo = await cobrar_creditos(user_id, "hsoat", usuarios)
    historial = res.get("historial") or []
    texto = (
        f"{titulo_sistema('HSOAT • RESULTADO', '🚗')}\n\n"
        f"🚘 Placa: <code>{error_html(res.get('placa', placa))}</code>\n"
        f"📊 Registros: <code>{error_html(res.get('cantidad_registros', len(historial)))}</code>\n\n"
    )
    for i, item in enumerate(historial, 1):
        texto += (
            f"📄 <b>SOAT #{i}</b>\n"
            f"🏢 Compañía: <code>{error_html(item.get('compania', '-'))}</code>\n"
            f"✅ Estado: <code>{error_html(item.get('estado', '-'))}</code>\n"
            f"📑 Póliza: <code>{error_html(item.get('poliza', '-'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💎 <b>DESCUENTO:</b> <code>{costo}</code> créditos\n💳 <b>SALDO:</b> <code>{saldo}</code> créditos\n⚜️ <b>SPECTER PERÚ</b>"
    await mensaje.edit_text(texto[:4090], parse_mode="HTML", reply_markup=BTN_VOLVER)


async def denpla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

    if len(context.args) != 1:
        return await update.message.reply_text(
            f"{titulo_sistema('DENUNCIAS POR PLACA', '🚨')}\n\nUso: <code>/denpla ABC123</code>\n💎 Costo: <code>{PRECIOS['denpla']}</code> créditos",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    placa = context.args[0].strip().upper()
    if not (3 <= len(placa) <= 8 and placa.isalnum()):
        return await responder_error(update, "La placa debe contener entre 3 y 8 caracteres alfanuméricos.")

    costo = await preparar_consulta(update, "denpla", usuarios, user_id)
    if costo is None:
        return

    mensaje = await update.message.reply_text(
        f"🔎 <b>CONSULTANDO DENUNCIAS VEHICULARES</b>\n🚗 Placa: <code>{placa}</code>\n💎 Costo: <code>{costo}</code> créditos",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/denpla/{placa}")
    if data.get("error"):
        return await editar_error(mensaje, data["error"])
    if not data.get("success"):
        return await editar_error(mensaje, data.get("message", "Placa no encontrada."))

    res = data.get("data") or {}
    saldo = await cobrar_creditos(user_id, "denpla", usuarios)
    denuncias_lista = res.get("denuncias") or []
    texto = (
        f"{titulo_sistema('DENUNCIAS POR PLACA', '🚨')}\n\n"
        f"🚗 Placa: <code>{error_html(res.get('placa', placa))}</code>\n"
        f"📊 Total: <code>{error_html(res.get('cantidad_denuncias', len(denuncias_lista)))}</code>\n\n"
    )
    for i, item in enumerate(denuncias_lista, 1):
        texto += (
            f"📌 <b>DENUNCIA #{i}</b>\n"
            f"Tipo: <code>{error_html(item.get('tipo', '-'))}</code>\n"
            f"Comisaría: <code>{error_html(item.get('comisaria', '-'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💎 <b>DESCUENTO:</b> <code>{costo}</code> créditos\n💳 <b>SALDO:</b> <code>{saldo}</code> créditos\n⚜️ <b>SPECTER PERÚ</b>"
    await mensaje.edit_text(texto[:4090], parse_mode="HTML", reply_markup=BTN_VOLVER)


async def suel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)

    if len(context.args) != 1:
        return await update.message.reply_text(
            f"{titulo_sistema('CONSULTA DE SUELDOS', '💼')}\n\nUso: <code>/suel 12345678</code>\n💎 Costo: <code>{PRECIOS['suel']}</code> créditos",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    dni_num = context.args[0].strip()
    if not (dni_num.isdigit() and len(dni_num) == 8):
        return await responder_error(update, "El DNI debe contener exactamente 8 dígitos.")

    costo = await preparar_consulta(update, "suel", usuarios, user_id)
    if costo is None:
        return

    mensaje = await update.message.reply_text(
        f"💼 <b>CONSULTANDO SUELDOS</b>\n🪪 DNI: <code>{dni_num}</code>\n💎 Costo: <code>{costo}</code> créditos",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )
    data = await consultar_api_get(f"{BASE_URL}/api/v1/consultas/fd/suel/{dni_num}")
    if data.get("error"):
        return await editar_error(mensaje, data["error"])
    if not data.get("success"):
        return await editar_error(mensaje, data.get("message", "No se encontraron registros."))

    res = data.get("data") or {}
    sueldos = res.get("sueldos") or []
    if not sueldos:
        return await editar_error(mensaje, "No se encontraron registros.")

    saldo = await cobrar_creditos(user_id, "suel", usuarios)
    texto = (
        f"{titulo_sistema('CONSULTA SUELDOS', '💼')}\n\n"
        f"🪪 DNI: <code>{error_html(res.get('consulta', dni_num))}</code>\n"
        f"📋 Total: <code>{error_html(res.get('total_registros', len(sueldos)))}</code>\n\n"
    )
    for i, item in enumerate(sueldos, 1):
        texto += (
            f"📊 <b>REGISTRO #{i}</b>\n"
            f"🏢 Empresa: <code>{error_html(item.get('empresa', '-'))}</code>\n"
            f"🪪 RUC: <code>{error_html(item.get('ruc', '-'))}</code>\n"
            f"📅 Periodo: <code>{error_html(item.get('periodo', '-'))}</code>\n"
            f"👔 Situación: <code>{error_html(item.get('situacion', '-'))}</code>\n"
            f"💰 Sueldo: <code>{error_html(item.get('sueldo', '-'))}</code>\n"
            f"{SEPARADOR}\n"
        )
    texto += f"💎 <b>DESCUENTO:</b> <code>{costo}</code> créditos\n💳 <b>SALDO:</b> <code>{saldo}</code> créditos\n⚜️ <b>SPECTER PERÚ</b>"
    await mensaje.edit_text(texto[:4090], parse_mode="HTML", reply_markup=BTN_VOLVER)


# ============================================================
# COMANDOS GENERALES
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        f"{titulo_sistema('SPECTER PERÚ', '⚜️')}\n\n"
        "🚀 <b>PLATAFORMA DE CONSULTAS</b>\n\n"
        f"🏷️ Nombre: <b>{html.escape(BOT_NAME)}</b>\n"
        f"👤 Usuario: <b>{html.escape(BOT_USER)}</b>\n"
        "🛰️ Estado: <b>ONLINE</b>\n\n"
        f"{SEPARADOR}\n"
        "📚 <b>COMANDOS</b>\n\n"
        "📝 /register ➜ Registrar cuenta\n"
        "📖 /cmds ➜ Ver servicios\n"
        "👤 /me ➜ Ver perfil\n"
        "🛡️ /staff ➜ Ver staff\n"
        "💳 /buy ➜ Planes y créditos\n\n"
        f"{SEPARADOR}\n"
        "⚡ Sistema actualizado y centralizado"
    )
    await update.message.reply_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)


async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        f"{titulo_sistema('MENÚ DE SERVICIOS', '🛰️')}\n\n"
        "🚀 <b>SISTEMA CENTRAL DE CONSULTAS</b>\n\n"
        "💎 Cada servicio muestra su costo.\n"
        "⚡ Los créditos se descuentan únicamente cuando la API confirma una consulta exitosa.\n"
        "🛡️ Si la API falla o no devuelve resultados, no se cobra.\n\n"
        f"{SEPARADOR}\n"
        "👇 <b>SELECCIONA UNA CATEGORÍA</b>"
    )
    await update.message.reply_text(texto, parse_mode="HTML", reply_markup=menu_teclado())


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id = str(update.effective_user.id)
    if user_id in usuarios:
        return await update.message.reply_text(
            f"{titulo_sistema('REGISTRO', '📝')}\n\n⚠️ Ya tienes una cuenta registrada.",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    usuarios[user_id] = {
        "creditos": 0,
        "consultas": 0,
        "nombre": update.effective_user.first_name or "Usuario",
        "username": update.effective_user.username or "",
        "fecha_registro": get_fecha(),
        "rol": "PENDIENTE",
        "plan": "FREE",
    }
    guardar_usuarios(usuarios)
    await update.message.reply_text(
        f"{titulo_sistema('REGISTRO COMPLETADO', '✅')}\n\n"
        f"👤 Bienvenido, <b>{html.escape(update.effective_user.first_name or 'Usuario')}</b>\n"
        "💳 Créditos: <code>0</code>\n"
        "💎 Usa /buy para recargar.",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )


async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuarios = cargar_usuarios()
    user_id, usuario = obtener_usuario(update, usuarios)
    guardar_usuarios(usuarios)
    username = f"@{usuario.get('username')}" if usuario.get("username") else "Sin username"

    texto = (
        f"{titulo_sistema('PERFIL DE USUARIO', '👤')}\n\n"
        f"👤 Nombre: <code>{error_html(usuario.get('nombre', 'Usuario'))}</code>\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📱 Usuario: <code>{error_html(username)}</code>\n"
        f"💳 Créditos: <code>{usuario.get('creditos', 0)}</code>\n"
        f"📊 Consultas: <code>{usuario.get('consultas', 0)}</code>\n"
        f"⭐ Plan: <code>{error_html(usuario.get('plan', 'FREE'))}</code>\n"
        f"🛡️ Rol: <code>{error_html(usuario.get('rol', 'PENDIENTE'))}</code>\n\n"
        f"{SEPARADOR}\n⚜️ <b>SPECTER PERÚ</b>"
    )
    await update.message.reply_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        f"{titulo_sistema('PLANES PREMIUM', '💎')}\n\n"
        "💰 <b>CRÉDITOS</b>\n\n"
        "🥉 100 créditos ➜ S/ 10\n"
        "🥈 200 créditos ➜ S/ 20\n"
        "🥇 400 créditos ➜ S/ 30\n"
        "💠 500 créditos ➜ S/ 40\n"
        "🚀 800 créditos ➜ S/ 50\n"
        "👑 2,000 créditos ➜ S/ 100\n"
        "💎 4,300 créditos ➜ S/ 200\n\n"
        f"{SEPARADOR}\n"
        "♾️ <b>PLANES ILIMITADOS</b>\n\n"
        "💥 7 días ➜ S/ 20\n"
        "⚡ 15 días ➜ S/ 35\n"
        "🔱 30 días ➜ S/ 60\n"
        "👑 60 días ➜ S/ 100\n\n"
        f"{SEPARADOR}\n"
        "💳 <b>PAGOS:</b> Yape • Plin • BCP\n"
        "👤 <b>CONTACTO:</b> @Sthep_18\n\n"
        "⚡ Atención rápida\n"
        "🛡️ Activación mediante administración"
    )
    await update.message.reply_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)


async def staff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        f"{titulo_sistema('STAFF OFICIAL', '👑')}\n\n"
        "🛡️ <b>ADMINISTRADOR PRINCIPAL</b>\n"
        "👤 @Sthep_18\n\n"
        f"{SEPARADOR}\n"
        "💳 Venta de créditos\n"
        "♾️ Planes premium\n"
        "🛠️ Soporte técnico\n"
        "📞 Atención personalizada\n\n"
        f"{SEPARADOR}\n"
        "⚜️ <b>SPECTER PERÚ</b>"
    )
    await update.message.reply_text(texto, parse_mode="HTML", reply_markup=BTN_VOLVER)


# ============================================================
# ADMINISTRACIÓN DE CRÉDITOS
# ============================================================
def es_admin(user_id: str) -> bool:
    return bool(user_id and user_id in ADMIN_ID)


async def quitarcrd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not es_admin(user_id):
        return await update.message.reply_text(
            f"{titulo_sistema('ACCESO DENEGADO', '🚫')}\n\nNo tienes permisos para este comando.",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    if len(context.args) != 2:
        return await update.message.reply_text(
            "Uso: <code>/quitarcrd ID_USUARIO CANTIDAD</code>",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    target_id = context.args[0]
    try:
        cantidad = int(context.args[1])
    except ValueError:
        return await responder_error(update, "La cantidad debe ser un número entero.")
    if cantidad <= 0:
        return await responder_error(update, "La cantidad debe ser mayor que cero.")

    usuarios = cargar_usuarios()
    if target_id not in usuarios:
        return await responder_error(update, f"El usuario {target_id} no existe.")

    saldo_anterior = int(usuarios[target_id].get("creditos", 0) or 0)
    usuarios[target_id]["creditos"] = max(0, saldo_anterior - cantidad)
    guardar_usuarios(usuarios)

    await update.message.reply_text(
        f"{titulo_sistema('CRÉDITOS QUITADOS', '➖')}\n\n"
        f"👤 Usuario: <code>{target_id}</code>\n"
        f"➖ Quitados: <code>{cantidad}</code>\n"
        f"💰 Anterior: <code>{saldo_anterior}</code>\n"
        f"💳 Actual: <code>{usuarios[target_id]['creditos']}</code>",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )


async def addcreditos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not es_admin(user_id):
        return await update.message.reply_text(
            f"{titulo_sistema('ACCESO DENEGADO', '🚫')}\n\nNo tienes permisos para este comando.",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    if len(context.args) != 2:
        return await update.message.reply_text(
            "Uso: <code>/addcreditos ID_USUARIO CANTIDAD</code>",
            parse_mode="HTML",
            reply_markup=BTN_VOLVER,
        )

    target_id = context.args[0]
    try:
        cantidad = int(context.args[1])
    except ValueError:
        return await responder_error(update, "La cantidad debe ser un número entero.")
    if cantidad <= 0:
        return await responder_error(update, "La cantidad debe ser mayor que cero.")

    usuarios = cargar_usuarios()
    if target_id not in usuarios:
        return await responder_error(update, f"El usuario {target_id} no existe.")

    saldo_anterior = int(usuarios[target_id].get("creditos", 0) or 0)
    usuarios[target_id]["creditos"] = saldo_anterior + cantidad
    guardar_usuarios(usuarios)

    await update.message.reply_text(
        f"{titulo_sistema('CRÉDITOS AGREGADOS', '➕')}\n\n"
        f"👤 Usuario: <code>{target_id}</code>\n"
        f"➕ Agregados: <code>{cantidad}</code>\n"
        f"💰 Anterior: <code>{saldo_anterior}</code>\n"
        f"💳 Actual: <code>{usuarios[target_id]['creditos']}</code>",
        parse_mode="HTML",
        reply_markup=BTN_VOLVER,
    )


# ============================================================
# MENÚ INTERACTIVO
# ============================================================
def textos_categoria() -> Dict[str, str]:
    return {
        "cmd_reniec": (
            f"{titulo_sistema('RENIEC', '🪪')}\n\n"
            f"1. /dni 12345678 ➜ {PRECIOS['dni']} créditos\n"
            f"2. /dnit 12345678 ➜ {PRECIOS['dnit']} créditos\n"
            f"3. /agv 12345678 ➜ {PRECIOS['agv']} créditos"
        ),
        "cmd_ruc": (
            f"{titulo_sistema('RUC', '🏢')}\n\n"
            f"💎 Precio configurado: <code>{PRECIOS['ruc']}</code> créditos\n"
            "⚠️ El archivo original no contiene una función /ruc implementada ni una ruta API confirmada, por lo que no se inventa una ruta."
        ),
        "cmd_vehiculos": (
            f"{titulo_sistema('VEHÍCULOS', '🚘')}\n\n"
            f"/hsoat ABC123 ➜ {PRECIOS['hsoat']} créditos\n"
            f"/denpla ABC123 ➜ {PRECIOS['denpla']} créditos\n"
            f"/placa ABC123 ➜ {PRECIOS['placa']} créditos (sin handler en el archivo original)"
        ),
        "cmd_telefono": (
            f"{titulo_sistema('TELEFONÍA', '📱')}\n\n"
            f"/telp 12345678 ➜ {PRECIOS['telp']} créditos\n"
            f"/telpcel 900000001 ➜ {PRECIOS['telpcel']} créditos"
        ),
        "cmd_denuncia": (
            f"{titulo_sistema('DENUNCIAS', '⚖️')}\n\n"
            f"/den 12345678 ➜ {PRECIOS['denuncia']} créditos\n"
            f"/denuncias 12345678 ➜ 30 créditos"
        ),
        "cmd_sueldo": (
            f"{titulo_sistema('SUELDOS', '💰')}\n\n"
            f"/suel 12345678 ➜ {PRECIOS['suel']} créditos"
        ),
        "cmd_facial": (
            f"{titulo_sistema('FACIAL', '🧬')}\n\n"
            f"Envía una foto con <code>/facial</code> en el caption.\n"
            f"💎 Precio: <code>{PRECIOS['facial']}</code> créditos"
        ),
        "cmd_buy": (
            f"{titulo_sistema('PLANES PREMIUM', '💎')}\n\n"
            "Usa /buy para ver los planes y métodos de contacto."
        ),
    }


async def editar_menu_o_texto(query, texto: str, teclado: InlineKeyboardMarkup) -> None:
    try:
        await query.edit_message_caption(
            caption=texto,
            parse_mode="HTML",
            reply_markup=teclado,
        )
    except Exception:
        try:
            await query.edit_message_text(
                texto,
                parse_mode="HTML",
                reply_markup=teclado,
            )
        except Exception:
            logger.exception("No se pudo editar mensaje del menú")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    if query.data in {"volver_cmds", "menu_inicio"}:
        texto = (
            f"{titulo_sistema('MENÚ DE SERVICIOS', '🛰️')}\n\n"
            "🚀 <b>SISTEMA CENTRAL DE CONSULTAS</b>\n\n"
            "💎 Selecciona una categoría.\n"
            "⚡ Todos los servicios muestran su costo.\n"
            "🛡️ El cobro se realiza solamente tras una respuesta exitosa."
        )
        return await editar_menu_o_texto(query, texto, menu_teclado())

    textos = textos_categoria()
    if query.data in textos:
        teclado = InlineKeyboardMarkup(
            [[InlineKeyboardButton("⬅️ VOLVER AL MENÚ", callback_data="volver_cmds")]]
        )
        return await editar_menu_o_texto(query, textos[query.data], teclado)


# ============================================================
# MAIN / HANDLERS
# ============================================================
def validar_configuracion() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Falta la variable de entorno BOT_TOKEN.")
    if not API_TOKEN:
        logger.warning("API_TOKEN no está configurado. Las consultas API fallarán hasta configurarlo.")


def main():
    validar_configuracion()
    keep_alive()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Callbacks
    application.add_handler(CallbackQueryHandler(button_handler))

    # Generales
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cmds", cmds))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("me", me))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("staff", staff))

    # Administración
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
    application.add_handler(CommandHandler("facial", facial))
    application.add_handler(CommandHandler("hsoat", hsoat))
    application.add_handler(CommandHandler("denpla", denpla))
    application.add_handler(CommandHandler("suel", suel))
    application.add_handler(CommandHandler("micelular", micelular))
    application.add_handler(CommandHandler("pagar", pagar))
    application.add_handler(CommandHandler("saldo", saldo))

    # /facial mediante foto + caption
    application.add_handler(
        MessageHandler(
            filters.PHOTO & filters.CaptionRegex(r"^/facial(?:\s|$)"),
            facial,
        )
    )

    logger.info("🚀 SPECTER PERÚ ONLINE")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()