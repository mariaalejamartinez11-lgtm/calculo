# 🧮 Asistente Virtual de Cálculo — Web

App de cálculo simbólico con entrada por texto o voz, desplegable en la web con Streamlit.

## 🚀 Deploy en Streamlit Cloud (gratis)

1. Sube el repo a GitHub
2. Entra a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu cuenta de GitHub
4. Selecciona el repo → archivo principal: `app.py`
5. Haz clic en **Deploy** — listo en ~2 minutos

El start command que Streamlit Cloud usa automáticamente es:
```
streamlit run app.py
```

## 💻 Correr localmente

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

pip install -r requirements.txt
streamlit run app.py
```

## 🎙️ Micrófono

El reconocimiento de voz usa la **Web Speech API** del navegador — sin costo, sin API key. Requiere **Chrome** (Firefox no la soporta aún).

## 📦 Stack

| Librería | Uso |
|---|---|
| `streamlit` | Interfaz web |
| `sympy` | Cálculo simbólico |
| `matplotlib` + `numpy` | Graficación |
| `python-dotenv` | Variables de entorno |

## 🗣️ Ejemplos

| Entrada | Resultado |
|---|---|
| `derivar x**2 + 3*x` | `2*x + 3` |
| `integrar sin(x)` | `-cos(x) + C` |
| `limite de x**2 cuando x tiende a 0` | `0` |
| `factorizar x**2 - 5*x + 6` | `(x-2)(x-3)` |
| `graficar x**2` | Gráfica interactiva |
