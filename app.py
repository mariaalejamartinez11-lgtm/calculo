import streamlit as st
import streamlit.components.v1 as components
from sympy import *
import matplotlib.pyplot as plt
import numpy as np
from openai import OpenAI
import fitz
from PIL import Image
import pytesseract
import base64
import os
import platform
from dotenv import load_dotenv

# Ruta de Tesseract: Windows local vs Linux (Render)
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

load_dotenv()

cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

x = symbols("x")

# ── Configuración de página ───────────────────────────────────────────────────

st.set_page_config(
    page_title="Asistente Virtual de Cálculo",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
    body { background-color: #1e1e1e; }
    .stApp { background-color: #1e1e1e; color: white; }
    .stTextInput > div > div > input {
        background-color: #111111;
        color: white;
        border: 2px solid #5ee83b;
        font-size: 18px;
    }
    .stButton > button {
        font-size: 15px;
        font-weight: bold;
        border-radius: 8px;
        border: none;
    }
    .resultado-box {
        background-color: #111111;
        border: 1px solid #5ee83b;
        border-radius: 8px;
        padding: 16px;
        font-size: 15px;
        color: white;
        white-space: pre-wrap;
        min-height: 120px;
    }
    h1 { color: #5ee83b !important; }
    .stTabs [data-baseweb="tab"] { color: white; }
</style>
""", unsafe_allow_html=True)

# ── Estado de sesión ──────────────────────────────────────────────────────────

if "historial" not in st.session_state:
    st.session_state.historial = []
if "texto_pdf" not in st.session_state:
    st.session_state.texto_pdf = ""
if "pantalla" not in st.session_state:
    st.session_state.pantalla = "inicio"

# ── Funciones de lógica ───────────────────────────────────────────────────────

def convertir_voz_a_formula(texto):
    texto = texto.lower()
    reemplazos = [
        ("equis", "x"), ("x al cuadrado", "x**2"), ("x al cubo", "x**3"),
        ("al cuadrado", "**2"), ("al cubo", "**3"), ("más", "+"), ("mas", "+"),
        ("menos", "-"), ("por", "*"), ("entre", "/"), ("seno de x", "sin(x)"),
        ("coseno de x", "cos(x)"), ("tangente de x", "tan(x)"),
        ("seno", "sin"), ("coseno", "cos"), ("tangente", "tan"),
        ("^", "**"), ("²", "**2"), ("³", "**3"), ("⁴", "**4"), ("⁵", "**5"),
        ("x cuadrado", "x**2"), ("x cubo", "x**3"),
        ("deriva", "derivar"), ("derívame", "derivar"),
        ("integral de", "integrar"), ("integra", "integrar"),
        ("grafica", "graficar"), ("gráfica", "graficar"), ("grafícame", "graficar"),
    ]
    for original, nuevo in reemplazos:
        texto = texto.replace(original, nuevo)
    return texto

def formato_bonito(texto):
    texto = str(texto)
    texto = texto.replace("**2", "²").replace("**3", "³")
    texto = texto.replace("**4", "⁴").replace("**5", "⁵")
    texto = texto.replace("*", "·")
    texto = texto.replace("sqrt", "√").replace("pi", "π").replace("oo", "∞")
    texto = texto.replace("sin", "sen")
    return texto

def explicar_paso_a_paso(tipo, funcion, resultado):
    if tipo == "derivar":
        return (f"Paso 1: Identificamos f(x) = {funcion}\n"
                f"Paso 2: Aplicamos la regla de derivación.\n"
                f"Paso 3: f'(x) = {resultado}")
    elif tipo == "integrar":
        return (f"Paso 1: Identificamos f(x) = {funcion}\n"
                f"Paso 2: Aplicamos la regla de integración.\n"
                f"Paso 3: ∫f(x)dx = {resultado} + C")
    return f"Resultado: {resultado}"

def preguntar_ia(pregunta):
    contexto = f"""
    Usa el siguiente contenido del libro si es relevante:
    {st.session_state.texto_pdf[:12000]}

    Pregunta: {pregunta}
    """
    respuesta = cliente.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": contexto}]
    )
    return respuesta.choices[0].message.content

def crear_imagen_ia(prompt):
    respuesta = cliente.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        response_format="b64_json"
    )
    return base64.b64decode(respuesta.data[0].b64_json)

def graficar(funcion_str):
    funcion_sympy = sympify(funcion_str)
    f = lambdify(x, funcion_sympy, "numpy")
    xs = np.linspace(-10, 10, 400)
    ys = f(xs)

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(xs, ys, color="#5ee83b", linewidth=2.5)
    ax.set_facecolor("#1e1e1e")
    fig.patch.set_facecolor("#1e1e1e")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("white")
    ax.axhline(0, color="white", linewidth=0.8)
    ax.axvline(0, color="white", linewidth=0.8)
    ax.grid(True, color="gray", alpha=0.3)
    ax.set_title(f"f(x) = {funcion_str}", color="white", fontsize=14)
    return fig

def procesar_operacion(orden):
    orden = convertir_voz_a_formula(orden)

    if "libro" in orden or "segun el libro" in orden:
        return preguntar_ia(orden), None

    if "crea una imagen" in orden:
        prompt = orden.replace("crea una imagen", "").strip()
        img_bytes = crear_imagen_ia(prompt)
        return "🎨 Imagen generada:", img_bytes

    if orden.startswith(("ia ", "ai ", "chat ")):
        pregunta = orden.split(" ", 1)[1].strip()
        return preguntar_ia(pregunta), None

    elif "derivar" in orden or "derivada" in orden:
        funcion = orden.replace("derivar", "").replace("derivada", "").strip()
        resultado = diff(sympify(funcion), x)
        return explicar_paso_a_paso("derivar", funcion, resultado), None

    elif "integrar" in orden or "integral" in orden:
        funcion = orden.replace("integrar", "").replace("integral", "").strip()
        resultado = integrate(sympify(funcion), x)
        return explicar_paso_a_paso("integrar", funcion, resultado), None

    elif "limite" in orden or "límite" in orden:
        partes = orden.replace("límite", "limite").replace("limite de", "").split("cuando x tiende a")
        if len(partes) == 2:
            funcion, punto = partes[0].strip(), partes[1].strip()
            resultado = limit(sympify(funcion), x, sympify(punto))
            return (f"Paso 1: f(x) = {funcion}\n"
                    f"Paso 2: x → {punto}\n"
                    f"Paso 3: Resultado = {resultado}"), None
        return "⚠️ Formato: `limite de [función] cuando x tiende a [valor]`", None

    elif "simplificar" in orden:
        funcion = orden.replace("simplificar", "").strip()
        resultado = simplify(sympify(funcion))
        return (f"Paso 1: Expresión: {funcion}\n"
                f"Paso 2: Simplificamos.\n"
                f"Paso 3: Resultado = {resultado}"), None

    elif "factorizar" in orden:
        funcion = orden.replace("factorizar", "").strip()
        resultado = factor(sympify(funcion))
        return (f"Paso 1: Expresión: {funcion}\n"
                f"Paso 2: Buscamos factores.\n"
                f"Paso 3: Resultado = {resultado}"), None

    elif "expandir" in orden:
        funcion = orden.replace("expandir", "").strip()
        resultado = expand(sympify(funcion))
        return (f"Paso 1: Expresión: {funcion}\n"
                f"Paso 2: Distribuimos.\n"
                f"Paso 3: Resultado = {resultado}"), None

    elif "resolver" in orden:
        funcion = orden.replace("resolver", "").strip()
        resultado = solve(sympify(funcion), x)
        return (f"Paso 1: Ecuación: {funcion} = 0\n"
                f"Paso 2: Despejamos x.\n"
                f"Paso 3: x = {resultado}"), None

    elif "graficar" in orden or "grafica" in orden:
        funcion = orden.replace("graficar", "").replace("grafica", "").strip()
        return f"__graficar__{funcion}", None

    elif any(op in orden for op in ["+", "-", "*", "/"]):
        resultado = simplify(sympify(orden))
        return (f"Paso 1: Operación: {orden}\n"
                f"Paso 3: Resultado = {resultado}"), None

    else:
        return preguntar_ia(orden), None

# ── Web Speech API ────────────────────────────────────────────────────────────

SPEECH_JS = """
<div style="text-align:center;padding:4px 0">
  <button id="micBtn" onclick="startListening()"
    style="background:#5ee83b;color:#000;border:none;border-radius:8px;
           padding:10px 28px;font-size:15px;font-weight:bold;cursor:pointer">
    🎙️ Hablar
  </button>
  <p id="status" style="color:#aaa;font-size:13px;margin:6px 0 0">Listo — usa Chrome</p>
</div>
<script>
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
function startListening() {
  if (!SR) { document.getElementById('status').textContent='⚠️ Solo funciona en Chrome'; return; }
  const rec = new SR();
  rec.lang = 'es-GT'; rec.interimResults = false; rec.maxAlternatives = 1;
  document.getElementById('micBtn').textContent = '⏳ Escuchando...';
  document.getElementById('status').textContent = 'Di tu operación...';
  rec.start();
  rec.onresult = (e) => {
    const t = e.results[0][0].transcript;
    document.getElementById('status').textContent = '✅ ' + t;
    document.getElementById('micBtn').textContent = '🎙️ Hablar';
    window.parent.postMessage({type:'speech', text:t}, '*');
  };
  rec.onerror = (e) => {
    document.getElementById('status').textContent = '❌ ' + e.error;
    document.getElementById('micBtn').textContent = '🎙️ Hablar';
  };
  rec.onend = () => { document.getElementById('micBtn').textContent = '🎙️ Hablar'; };
}
</script>
"""

# ── Pantalla de inicio ────────────────────────────────────────────────────────

if st.session_state.pantalla == "inicio":
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center;font-size:48px'>🤖</h1>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center'>Asistente Virtual de Cálculo</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#ccc;font-size:18px'>Hola! Soy tu Asistente Virtual<br>¿Necesitas ayuda por medio de:</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        if st.button("⌨️  Texto", use_container_width=True):
            st.session_state.pantalla = "principal"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🎙️  Voz", use_container_width=True):
            st.session_state.pantalla = "principal"
            st.rerun()
    st.stop()

# ── Pantalla principal ────────────────────────────────────────────────────────

st.markdown("# 🤖 Asistente Virtual de Cálculo")

tab_calc, tab_ia, tab_pdf, tab_imagen, tab_historial = st.tabs([
    "🧮 Calculadora", "🤖 IA / Chat", "📄 PDF", "🎨 Imagen", "📋 Historial"
])

# ── TAB 1: Calculadora ────────────────────────────────────────────────────────

with tab_calc:
    st.markdown("### Escribe o usa el micrófono")

    orden = st.text_input("Operación", placeholder="ej: derivar x**2 + 3*x", label_visibility="collapsed")

    # Símbolos rápidos
    simbolos = [("x²","x**2"),("x³","x**3"),("√","sqrt()"),("sin","sin()"),
                ("cos","cos()"),("tan","tan()"),("π","pi"),("∞","oo"),
                ("∫","integrar "),("d/dx","derivar "),("lim","limite ")]
    cols = st.columns(len(simbolos))
    for i, (etiqueta, valor) in enumerate(simbolos):
        if cols[i].button(etiqueta, key=f"sim_{i}"):
            st.session_state["_insertar"] = valor

    if "_insertar" in st.session_state:
        orden = orden + st.session_state.pop("_insertar")

    col_r, col_l = st.columns([1, 1])
    calcular = col_r.button("▦ Resolver", use_container_width=True)
    limpiar  = col_l.button("🗑️ Limpiar",  use_container_width=True)

    if limpiar:
        orden = ""

    st.markdown("---")
    components.html(SPEECH_JS, height=90)
    st.markdown("---")

    if calcular and orden.strip():
        with st.spinner("Pensando... 🤖"):
            try:
                resultado, extra = procesar_operacion(orden.strip())

                # Imagen generada por IA
                if extra is not None:
                    st.image(extra, caption="Imagen generada", use_container_width=True)
                    st.session_state.historial.insert(0, {"entrada": orden, "salida": "Imagen generada"})

                # Gráfica
                elif isinstance(resultado, str) and resultado.startswith("__graficar__"):
                    funcion_str = resultado.replace("__graficar__", "")
                    try:
                        fig = graficar(funcion_str)
                        st.pyplot(fig)
                        resultado_display = f"Gráfica de f(x) = {funcion_str}"
                    except Exception as e:
                        resultado_display = f"⚠️ No se pudo graficar: {e}"
                    st.session_state.historial.insert(0, {"entrada": orden, "salida": resultado_display})

                # Resultado + explicación IA
                else:
                    resultado_bonito = formato_bonito(resultado)
                    st.markdown(f'<div class="resultado-box">{resultado_bonito}</div>', unsafe_allow_html=True)

                    with st.spinner("Generando explicación IA..."):
                        explicacion = preguntar_ia(
                            f"Explica brevemente este resultado matemático para un estudiante: "
                            f"operación '{orden}', resultado '{resultado}'"
                        )
                    st.markdown("**Explicación IA:**")
                    st.info(explicacion)

                    st.session_state.historial.insert(0, {"entrada": orden, "salida": resultado_bonito})

            except Exception as e:
                st.error(f"⚠️ Error: {e}")

    with st.expander("📖 Guía de comandos"):
        st.markdown("""
| Escribe... | Resultado |
|---|---|
| `derivar x**2 + 3*x` | Derivada paso a paso |
| `integrar sin(x)` | Integral + C |
| `limite de x**2 cuando x tiende a 0` | Límite |
| `simplificar (x**2-1)/(x-1)` | Simplificación |
| `factorizar x**2 - 5*x + 6` | Factorización |
| `resolver x**2 - 4` | Raíces |
| `graficar x**2` | Gráfica |
| `ia [pregunta]` | Chat con IA |
| `libro [pregunta]` | Consulta el PDF cargado |
| `crea una imagen [descripción]` | Imagen con DALL-E |
""")

# ── TAB 2: IA / Chat ──────────────────────────────────────────────────────────

with tab_ia:
    st.markdown("### Chat con IA")
    pregunta_ia = st.text_area("Tu pregunta:", height=100, placeholder="Explícame qué es una derivada...")
    if st.button("Preguntar a la IA", key="btn_ia"):
        if pregunta_ia.strip():
            with st.spinner("Consultando IA..."):
                respuesta = preguntar_ia(pregunta_ia)
            st.markdown("**Respuesta:**")
            st.success(respuesta)
            st.session_state.historial.insert(0, {"entrada": pregunta_ia, "salida": respuesta})

# ── TAB 3: PDF ────────────────────────────────────────────────────────────────

with tab_pdf:
    st.markdown("### Cargar libro / PDF")
    pdf_file = st.file_uploader("Sube un PDF", type=["pdf"])

    if pdf_file:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        texto = ""
        for pagina in doc:
            texto += pagina.get_text()
        st.session_state.texto_pdf = texto
        st.success(f"✅ PDF cargado — {len(texto)} caracteres extraídos")
        st.text_area("Vista previa:", texto[:2000] + "...", height=200)

    st.markdown("### Leer ejercicio desde imagen (OCR)")
    img_file = st.file_uploader("Sube una imagen del ejercicio", type=["png","jpg","jpeg"], key="ocr")

    if img_file:
        imagen = Image.open(img_file)
        try:
            texto_ocr = pytesseract.image_to_string(imagen, lang="eng+spa")
            if texto_ocr.strip():
                st.markdown("**Texto detectado:**")
                st.code(texto_ocr)
                if st.button("Resolver este ejercicio", key="btn_ocr"):
                    with st.spinner("Procesando..."):
                        resultado, _ = procesar_operacion(texto_ocr.strip())
                        st.markdown(f'<div class="resultado-box">{formato_bonito(resultado)}</div>', unsafe_allow_html=True)
            else:
                st.warning("No se detectó texto en la imagen. Asegúrate que el ejercicio sea legible.")
        except Exception as e:
            st.error(f"Error al leer la imagen: {e}")

# ── TAB 4: Imagen ─────────────────────────────────────────────────────────────

with tab_imagen:
    st.markdown("### Crear imagen con IA (DALL-E)")
    prompt_img = st.text_input("Describe la imagen:", placeholder="Un triángulo rectángulo con sus lados etiquetados")
    if st.button("🎨 Generar imagen"):
        if prompt_img.strip():
            with st.spinner("Generando imagen... puede tardar unos segundos"):
                try:
                    img_bytes = crear_imagen_ia(prompt_img)
                    st.image(img_bytes, caption=prompt_img, use_container_width=True)
                    st.download_button("⬇️ Descargar imagen", img_bytes, "imagen.png", "image/png")
                except Exception as e:
                    st.error(f"Error al generar imagen: {e}")

# ── TAB 5: Historial ──────────────────────────────────────────────────────────

with tab_historial:
    st.markdown("### Historial de operaciones")

    if st.session_state.historial:
        col_h, col_g = st.columns([3, 1])
        with col_g:
            historial_txt = "\n".join(
                f"{item['entrada']}  →  {item['salida']}"
                for item in st.session_state.historial
            )
            st.download_button("💾 Descargar .txt", historial_txt, "historial_calculo.txt")

        for item in st.session_state.historial:
            with st.expander(f"📥 `{item['entrada']}`"):
                st.markdown(item["salida"])
    else:
        st.info("Aún no hay operaciones en el historial.")
