import streamlit as st
from googleapiclient.discovery import build
import random
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Mi Sorteo YouTube", page_icon="🎉")

st.title("🎉 Sorteos de YouTube (Privado)")
st.write("Herramienta personal para elegir ganadores desde comentarios.")

# --- BARRA LATERAL PARA CONFIGURACIÓN ---
with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input("Tu API Key de Google", type="password")
    st.info("Pega aquí la clave que obtuviste en Google Cloud Console.")

# --- FUNCIONES ---
def obtener_id_video(url):
    """Extrae el ID del video de varios formatos de URL de YouTube"""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def obtener_comentarios(api_key, video_id, palabra_clave=None):
    youtube = build('youtube', 'v3', developerKey=api_key)
    comentarios = []
    
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100, # Trae de 100 en 100
            textFormat="plainText"
        )
        
        with st.spinner('Leyendo comentarios...'):
            while request:
                response = request.execute()
                
                for item in response['items']:
                    comentario = item['snippet']['topLevelComment']['snippet']
                    texto = comentario['textDisplay']
                    autor = comentario['authorDisplayName']
                    
                    # Filtro de palabra clave (si existe)
                    if palabra_clave:
                        if palabra_clave.lower() in texto.lower():
                            comentarios.append({"Autor": autor, "Comentario": texto})
                    else:
                        comentarios.append({"Autor": autor, "Comentario": texto})
                
                # Paginación (si hay más de 100 comentarios)
                if 'nextPageToken' in response:
                    request = youtube.commentThreads().list(
                        part="snippet",
                        videoId=video_id,
                        maxResults=100,
                        textFormat="plainText",
                        pageToken=response['nextPageToken']
                    )
                else:
                    break
        return comentarios
            
    except Exception as e:
        st.error(f"Error al conectar con YouTube: {e}")
        return []

# --- INTERFAZ PRINCIPAL ---
url_video = st.text_input("Pegar enlace del video de YouTube:")
palabra_filtro = st.text_input("Palabra clave obligatoria (Opcional):", placeholder="Ej: participo")

if st.button("¡Cargar Comentarios!", type="primary"):
    if not api_key:
        st.warning("Por favor ingresa tu API Key en la barra lateral.")
    elif not url_video:
        st.warning("Por favor ingresa un enlace de video.")
    else:
        video_id = obtener_id_video(url_video)
        if video_id:
            participantes = obtener_comentarios(api_key, video_id, palabra_filtro)
            
            if participantes:
                st.success(f"¡Se encontraron {len(participantes)} participantes válidos!")
                
                # Guardar en sesión para no perderlos al hacer click en sortear
                st.session_state['participantes'] = participantes
            else:
                st.warning("No se encontraron comentarios (o ninguno con la palabra clave).")
        else:
            st.error("URL de video no válida.")

# --- SECCIÓN DE SORTEO ---
if 'participantes' in st.session_state and len(st.session_state['participantes']) > 0:
    st.divider()
    st.subheader("🏆 Zona de Ganadores")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✨ Elegir Ganador Aleatorio"):
            ganador = random.choice(st.session_state['participantes'])
            st.balloons() # ¡Efecto de globos!
            st.markdown(f"### El ganador es:")
            st.markdown(f"# 👤 {ganador['Autor']}")
            st.info(f"Comentario: {ganador['Comentario']}")

    with col2:
        with st.expander("Ver lista de participantes"):
            st.table(st.session_state['participantes'])
