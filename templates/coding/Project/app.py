import streamlit as st
import numpy as np
import plotly.express as px
import sympy as sp


st.set_page_config(page_title="Mathematik Demo", layout="wide")

st.title("Mathematik Demo — Interaktive Visualisierungen")
st.write("Eine kleine Demo in Deutsch mit interaktiven Plots und Formeln.")

demo = st.sidebar.selectbox("Demo wählen", ["Quadratische Funktion", "Sinuswellen"])

if demo == "Quadratische Funktion":
    st.header("Quadratische Funktion")
    st.write("$f(x)=ax^2 + bx + c$ — Parameter wählen und Ableitung ansehen.")

    col1, col2 = st.columns(2)

    with col1:
        a = st.slider("a", -5.0, 5.0, 1.0, 0.1)
        b = st.slider("b", -10.0, 10.0, 0.0, 0.1)
        c = st.slider("c", -10.0, 10.0, 0.0, 0.1)
        x_min, x_max = st.slider("x-Bereich", -10.0, 10.0, (-5.0, 5.0), 0.5)

    x = np.linspace(x_min, x_max, 400)
    y = a * x ** 2 + b * x + c

    # Anzeige der Formel mit Sympy
    x_sym = sp.symbols('x')
    f_sym = a * x_sym ** 2 + b * x_sym + c
    f_prime = sp.diff(f_sym, x_sym)

    st.latex(sp.latex(f_sym))
    st.markdown("**Ableitung:**")
    st.latex(sp.latex(f_prime))

    fig = px.line(x=x, y=y, labels={'x': 'x', 'y': 'f(x)'}, title='Quadratische Funktion')
    st.plotly_chart(fig, use_container_width=True)

    # Scheitelpunkt
    if a != 0:
        xv = -b / (2 * a)
        yv = a * xv ** 2 + b * xv + c
        st.write(f"Scheitelpunkt: x={xv:.3f}, f(x)={yv:.3f}")

else:
    st.header("Sinuswellen")
    st.write("Interaktiver Sinusplot mit Amplitude, Frequenz und Phase.")

    amp = st.slider("Amplitude", 0.0, 5.0, 1.0, 0.1)
    freq = st.slider("Frequenz (Hz)", 0.1, 10.0, 1.0, 0.1)
    phase = st.slider("Phase (rad)", 0.0, 2 * np.pi, 0.0, 0.1)
    t_end = st.slider("Zeit (s)", 0.5, 10.0, 2.0, 0.5)

    t = np.linspace(0, t_end, 800)
    y = amp * np.sin(2 * np.pi * freq * t + phase)

    st.latex(r"f(t) = A \sin(2\pi f t + \phi)")
    fig = px.line(x=t, y=y, labels={'x': 't', 'y': 'f(t)'}, title='Sinuswelle')
    st.plotly_chart(fig, use_container_width=True)
