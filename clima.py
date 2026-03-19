import streamlit as st
import plotly.graph_objects as go
import requests
import google.generativeai as genai_old


#CONFIGURACIÓN DE TUS LLAVES

API_KEY_GOOGLE = st.secrets["GOOGLE_API_KEY"]
API_KEY_CLIMA = st.secrets["CLIMA_API_KEY"]

genai_old.configure(api_key=API_KEY_GOOGLE)
model_ia = genai_old.GenerativeModel('gemini-1.5-flash')


# FUNCIONES DE LÓGICA

def obtener_clima_api(ciudad):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad.strip()}&appid={API_KEY_CLIMA}&units=metric&lang=es"
        res = requests.get(url)
        if res.status_code == 200:
            datos = res.json()
            return datos['main']['humidity'], datos['weather'][0]['description']
        return 50, "Cielo despejado (estimado)"
    except:
        return 50, "Error de conexión"

def calcular_indice_calor(t, h):
    # Solo aplicamos fórmula de sensación térmica si hace calor (>14.5)
    if t > 14.5:
        return t + (0.55 * (1 - h/100) * (t - 14.5))
    return t 

# DISEÑO DE LA INTERFAZ
st.set_page_config(page_title="Monitor Climático Perú", layout="wide")

st.markdown("<h1 style='text-align: center;'>🌡️ Sistema de Alerta Inteligente</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("Entrada de Datos")
    ciudad = st.text_input("Ciudad:", "Arequipa")
    temp_usuario = st.number_input("Temperatura medida (°C):", value=15.0)
    btn = st.button("CALCULAR RIESGO")

if btn:
    
    humedad, descripcion = obtener_clima_api(ciudad)
    indice = calcular_indice_calor(temp_usuario, humedad)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📊 Análisis Matemático (HI)")
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = indice,
            gauge = {
                'axis': {'range': [0, 50]},
                'bar': {'color': "white"},
                'steps': [
                    {'range': [0, 15], 'color': "#87CEEB"},  # celeste Frío
                    {'range': [15, 30], 'color': "#2ECC71"}, # Verde Normal
                    {'range': [30, 40], 'color': "#F1C40F"}, # Amarillo Calor
                    {'range': [40, 50], 'color': "#E74C3C"}  # Rojo Peligro
                ],
            }
        ))
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
        
        st.info(f"**Estado en {ciudad}:** {descripcion.capitalize()}")

    with col2:
        
        st.subheader("💧 Nivel de Humedad")
        color_h = "#3498DB" if humedad > 70 else "#2ECC71"
        st.markdown(f"""
            <div style="background-color: #eee; border-radius: 10px; width: 100%;">
                <div style="background-color: {color_h}; width: {humedad}%; padding: 10px; border-radius: 10px; color: white; text-align: center; font-weight: bold;">
                    {humedad}% Humedad Detectada
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        
        st.subheader("📝 Notas Médicas y de Seguridad (IA)")
        with st.spinner("La IA está analizando el riesgo..."):
           
            tipo_clima = "FRÍO extremo" if temp_usuario < 18 else "CALOR extremo"
            prompt = f"""
            El usuario está en {ciudad} con {temp_usuario}°C y {humedad}% de humedad.
            Esto se considera {tipo_clima}. 
            Da 3 recomendaciones breves:
            1. Para la salud personal (abrigo/hidratación).
            2. Para el cuidado del hogar (ventilación/aislamiento).
            3. Un aviso sobre riesgos de la zona (como lluvias o huaycos si es Arequipa).
            """
            
            try:
               
                response = model_ia.generate_content(prompt)
                st.success(response.text)
            except Exception as e:
                st.error(f"Error de conexión con Google: {e}")
              
              
