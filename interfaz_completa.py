import tkinter as tk
import pyttsx3
import speech_recognition as sr
from sympy import *
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()
GOOGLE_SPEECH_API_KEY = os.getenv("GOOGLE_SPEECH_API_KEY")

x = symbols("x")
voz = pyttsx3.init()


def hablar(texto):
    print(texto)
    voz.say(str(texto))
    voz.runAndWait()


def escuchar():
    reconocedor = sr.Recognizer()

    with sr.Microphone() as source:
        hablar("Dime la operación matemática.")
        reconocedor.adjust_for_ambient_noise(source, duration=1)
        audio = reconocedor.listen(source)

    try:
        # Si hay API key configurada, úsala; si no, usa el modo gratuito
        if GOOGLE_SPEECH_API_KEY:
            texto = reconocedor.recognize_google_cloud(
                audio,
                credentials_json=GOOGLE_SPEECH_API_KEY,
                language="es-GT"
            )
        else:
            texto = reconocedor.recognize_google(audio, language="es-GT")
        return texto.lower()
    except:
        return ""


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


def derivar(funcion):
    return diff(sympify(funcion), x)


def integrar(funcion):
    return integrate(sympify(funcion), x)


def calcular_limite(funcion, punto):
    return limit(sympify(funcion), x, sympify(punto))


def simplificar(funcion):
    return simplify(sympify(funcion))


def factorizar(funcion):
    return factor(sympify(funcion))


def expandir_funcion(funcion):
    return expand(sympify(funcion))


def resolver_ecuacion(funcion):
    return solve(sympify(funcion), x)


def graficar_funcion(funcion):
    plot(sympify(funcion))


def procesar_operacion(orden):
    try:
        orden = convertir_voz_a_formula(orden)

        if "derivar" in orden or "derivada" in orden:
            funcion = orden.replace("derivar", "").replace("derivada", "").strip()
            resultado = derivar(funcion)
            mensaje = f"La derivada es {resultado}"
            hablar(mensaje)
            return mensaje

        elif "integrar" in orden or "integral" in orden:
            funcion = orden.replace("integrar", "").replace("integral", "").strip()
            resultado = integrar(funcion)
            mensaje = f"La integral es {resultado}"
            hablar(mensaje)
            return mensaje

        elif "limite" in orden or "límite" in orden:
            funcion = entrada.get()
            punto = entrada_punto.get() if 'entrada_punto' in globals() else "0"
            funcion = convertir_voz_a_formula(funcion)
            punto = convertir_voz_a_formula(punto)
            resultado = calcular_limite(funcion, punto)
            mensaje = f"El límite es {resultado}"
            hablar(mensaje)
            return mensaje

        elif "simplificar" in orden:
            funcion = orden.replace("simplificar", "").strip()
            resultado = simplificar(funcion)
            mensaje = f"La simplificación es {resultado}"
            hablar(mensaje)
            return mensaje

        elif "factorizar" in orden:
            funcion = orden.replace("factorizar", "").strip()
            resultado = factorizar(funcion)
            mensaje = f"La factorización es {resultado}"
            hablar(mensaje)
            return mensaje

        elif "expandir" in orden:
            funcion = orden.replace("expandir", "").strip()
            resultado = expandir_funcion(funcion)
            mensaje = f"La expansión es {resultado}"
            hablar(mensaje)
            return mensaje

        elif "resolver" in orden:
            funcion = orden.replace("resolver", "").strip()
            resultado = resolver_ecuacion(funcion)
            mensaje = f"La solución es {resultado}"
            hablar(mensaje)
            return mensaje

        elif "graficar" in orden:
            funcion = orden.replace("graficar", "").strip()
            graficar_funcion(funcion)
            mensaje = "Aquí está la gráfica."
            hablar(mensaje)
            return mensaje

        else:
            mensaje = "No reconozco esa operación."
            hablar(mensaje)
            return mensaje

    except Exception as error:
        mensaje = "Hubo un error. Revisa la función."
        hablar(mensaje)
        print(error)
        return mensaje


def resolver_desde_interfaz():
    orden = entrada.get()
    resultado = procesar_operacion(orden)
    resultado_label.config(text=resultado)


def usar_voz_interfaz():
    orden = escuchar()

    if orden == "":
        resultado_label.config(text="No logré entenderte.")
        hablar("No logré entenderte.")
        return

    entrada.delete(0, tk.END)
    entrada.insert(0, orden)

    resultado = procesar_operacion(orden)
    resultado_label.config(text=resultado)


ventana = tk.Tk()
ventana.title("Asistente Virtual de Cálculo")
ventana.geometry("700x450")

titulo = tk.Label(
    ventana,
    text="Asistente Virtual de Cálculo",
    font=("Arial", 22, "bold")
)
titulo.pack(pady=20)

entrada = tk.Entry(
    ventana,
    width=55,
    font=("Arial", 13)
)
entrada.pack(pady=10)

boton_resolver = tk.Button(
    ventana,
    text="Resolver",
    command=resolver_desde_interfaz,
    width=25,
    font=("Arial", 12)
)
boton_resolver.pack(pady=7)

boton_voz = tk.Button(
    ventana,
    text="Usar voz",
    command=usar_voz_interfaz,
    width=25,
    font=("Arial", 12)
)
boton_voz.pack(pady=7)

resultado_label = tk.Label(
    ventana,
    text="Resultado aquí",
    font=("Arial", 16),
    wraplength=600
)
resultado_label.pack(pady=25)

ventana.mainloop()
