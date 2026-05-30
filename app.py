import streamlit as st
import streamlit.components.v1 as components
from sympy import *
from dotenv import load_dotenv
import os

load_dotenv()

x = symbols("x")

st.set_page_config(
    page_title="Asistente Virtual de Cálculo",
    page_icon="🧮",
    layout="centered"
)

st.title("🧮 Asistente Virtual de Cálculo")
st.caption("Escribe una operación o usa el micrófono (requiere Chrome)")

# ── Lógica de cálculo ─────────────────────────────────────────────────────────

def convertir_voz_a_formula(texto):
    texto = texto.lower()
    texto = texto.replace("equis", "x")
    texto = texto.replace("x al cuadrado", "x**2")
    texto = texto.replace("x al cubo", "x**3")
    texto = texto.replace("al cuadrado", "**2")
    texto = texto.replace("al cubo", "**3")
    texto = texto.replace("más", "+")
    texto = texto.replace("mas", "+")
    texto = texto.replace("menos", "-")
    texto = texto.replace("por", "*")
    texto = texto.replace("entre", "/")
    texto = texto.replace("seno", "sin")
    texto = texto.replace("coseno", "cos")
    texto = texto.replace("tangente", "tan")
    texto = texto.replace("^", "**")
    return texto


def procesar_operacion(orden):
    orden = convertir_voz_a_formula(orden)

    if "derivar" in orden or "derivada" in orden:
        funcion = orden.replace("derivar", "").replace("derivada", "").strip()
        resultado = diff(sympify(funcion), x)
        return f"**Derivada:** `{resultado}`"

    elif "integrar" in orden or "integral" in orden:
        funcion = orden.replace("integrar", "").replace("integral", "").strip()
        resultado = integrate(sympify(funcion), x)
        return f"**Integral:** `{resultado} + C`"

    elif "limite" in orden or "límite" in orden:
        # Formato esperado: "limite de x**2 cuando x tiende a 0"
        partes = orden.replace("límite", "limite").replace("limite de", "").split("cuando x tiende a")
        if len(partes) == 2:
            funcion = partes[0].strip()
            punto = partes[1].strip()
            resultado = limit(sympify(funcion), x, sympify(punto))
            return f"**Límite:** `{resultado}`"
        return "⚠️ Formato: `limite de [función] cuando x tiende a [valor]`"

    elif "simplificar" in orden:
        funcion = orden.replace("simplificar", "").strip()
        resultado = simplify(sympify(funcion))
        return f"**Simplificación:** `{resultado}`"

    elif "factorizar" in orden:
        funcion = orden.replace("factorizar", "").strip()
        resultado = factor(sympify(funcion))
        return f"**Factorización:** `{resultado}`"

    elif "expandir" in orden:
        funcion = orden.replace("expandir", "").strip()
        resultado = expand(sympify(funcion))
        return f"**Expansión:** `{resultado}`"

    elif "resolver" in orden:
        funcion = orden.replace("resolver", "").strip()
        resultado = solve(sympify(funcion), x)
        return f"**Solución:** `x = {resultado}`"

    elif "graficar" in orden:
        funcion = orden.replace("graficar", "").strip()
        return f"__graficar__{funcion}"

    else:
        return "⚠️ No reconozco esa operación. Prueba con: derivar, integrar, simplificar, factorizar, expandir, resolver, graficar o límite."


# ── Web Speech API (micrófono en el browser) ──────────────────────────────────

SPEECH_COMPONENT = """
<div style="display:flex;flex-direction:column;align-items:center;gap:10px;padding:8px 0">
  <button id="micBtn" onclick="startListening()"
    style="background:#1D9E75;color:#fff;border:none;border-radius:8px;
           padding:10px 24px;font-size:15px;cursor:pointer;width:200px">
    🎙️ Hablar
  </button>
  <p id="status" style="color:#888;font-size:13px;margin:0">Listo</p>
  <input id="result" type="hidden" value="">
</div>

<script>
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

function startListening() {
  if (!SpeechRecognition) {
    document.getElementById('status').textContent = '⚠️ Usa Chrome para el micrófono';
    return;
  }
  const rec = new SpeechRecognition();
  rec.lang = 'es-GT';
  rec.interimResults = false;
  rec.maxAlternatives = 1;

  document.getElementById('micBtn').textContent = '⏳ Escuchando...';
  document.getElementById('status').textContent = 'Di tu operación...';

  rec.start();

  rec.onresult = (e) => {
    const texto = e.results[0][0].transcript;
    document.getElementById('status').textContent = '✅ Reconocido: ' + texto;
    document.getElementById('micBtn').textContent = '🎙️ Hablar';
    // Enviar al padre (Streamlit)
    window.parent.postMessage({type: 'speech', text: texto}, '*');
  };

  rec.onerror = (e) => {
    document.getElementById('status').textContent = '❌ Error: ' + e.error;
    document.getElementById('micBtn').textContent = '🎙️ Hablar';
  };

  rec.onend = () => {
    document.getElementById('micBtn').textContent = '🎙️ Hablar';
  };
}
</script>
"""

# ── Estado de sesión ──────────────────────────────────────────────────────────

if "historial" not in st.session_state:
    st.session_state.historial = []

if "orden_voz" not in st.session_state:
    st.session_state.orden_voz = ""

# ── UI principal ──────────────────────────────────────────────────────────────

col1, col2 = st.columns([3, 1])
with col1:
    orden_texto = st.text_input(
        "Operación",
        placeholder="ej: derivar x**2 + 3*x",
        label_visibility="collapsed"
    )
with col2:
    calcular = st.button("Calcular", use_container_width=True)

st.divider()

# Micrófono
components.html(SPEECH_COMPONENT, height=110)

# Capturar texto del micrófono via query param (workaround Streamlit)
orden_voz = st.query_params.get("voz", "")
if orden_voz and orden_voz != st.session_state.orden_voz:
    st.session_state.orden_voz = orden_voz
    orden_texto = orden_voz

st.divider()

# ── Procesar ──────────────────────────────────────────────────────────────────

orden_final = orden_texto.strip()

if calcular and orden_final:
    try:
        resultado = procesar_operacion(orden_final)

        # Graficar aparte
        if resultado.startswith("__graficar__"):
            funcion_str = resultado.replace("__graficar__", "")
            try:
                import numpy as np
                import matplotlib.pyplot as plt

                func = lambdify(x, sympify(funcion_str), "numpy")
                xs = np.linspace(-10, 10, 400)
                ys = func(xs)

                fig, ax = plt.subplots(figsize=(7, 3.5))
                ax.plot(xs, ys, color="#1D9E75", linewidth=2)
                ax.axhline(0, color="gray", linewidth=0.5)
                ax.axvline(0, color="gray", linewidth=0.5)
                ax.set_title(f"f(x) = {funcion_str}", fontsize=13)
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
                resultado_display = f"Gráfica de `{funcion_str}`"
            except Exception as e:
                resultado_display = f"⚠️ No se pudo graficar: {e}"
        else:
            resultado_display = resultado
            st.success(resultado)

        st.session_state.historial.insert(0, {
            "entrada": orden_final,
            "salida": resultado_display
        })

    except Exception as e:
        st.error(f"⚠️ Error al procesar: `{e}`")

# ── Historial ─────────────────────────────────────────────────────────────────

if st.session_state.historial:
    st.subheader("Historial")
    for item in st.session_state.historial[:8]:
        with st.expander(f"📥 `{item['entrada']}`"):
            st.markdown(item["salida"])

# ── Guía de uso ───────────────────────────────────────────────────────────────

with st.expander("📖 ¿Cómo usar?"):
    st.markdown("""
| Di o escribe... | Resultado |
|---|---|
| `derivar x**2 + 3*x` | Derivada |
| `integrar sin(x)` | Integral |
| `limite de x**2 cuando x tiende a 0` | Límite |
| `simplificar (x**2 - 1)/(x - 1)` | Simplificación |
| `factorizar x**2 - 5*x + 6` | Factorización |
| `expandir (x+1)**3` | Expansión |
| `resolver x**2 - 4` | Raíces |
| `graficar x**2` | Gráfica |
""")
