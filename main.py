import streamlit as st
from googleapiclient.discovery import build
import random
import re

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sorteos Pro", page_icon="🏆", layout="centered")

st.title("🎉 Sorteo de YouTube Pro")
st.write("Configura tus ganadores y suplentes fácilmente.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("Tu API Key de Google", type="password")
    
    st.divider()
    st.subheader("Opciones del Sorteo")
    num_ganadores = st.number_input("Número de ganadores", min_value=1, max_value=50, value=1)
    num_suplentes = st.number_input("Número de suplentes", min_value=0, max_value=10, value=0)
    
    st.info("Nota: Los suplentes se eligen de la lista restante después de sacar a los ganadores.")

# --- FUNCIONES ---
def obtener_id_video(url):
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
            maxResults=100,
            textFormat="plainText"
        )
        
        with st.spinner('Extrayendo comentarios de YouTube...'):
            while request:
                response = request.execute()
                for item in response['items']:
                    snippet = item['snippet']['topLevelComment']['snippet']
                    # El ID del comentario sirve para crear el enlace directo
                    comment_id = item['snippet']['topLevelComment']['id']
                    texto = snippet['textDisplay']
                    autor = snippet['authorDisplayName']
                    
                    datos = {
                        "Autor": autor, 
                        "Comentario": texto,
                        "Link": f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}"
                    }
                    
                    if palabra_clave:
                        if palabra_clave.lower() in texto.lower():
                            comentarios.append(datos)
                    else:
                        comentarios.append(datos)
                
                if 'nextPageToken' in response:
                    request = youtube.commentThreads().list(
                        part="snippet", videoId=video_id, maxResults=100,
                        textFormat="plainText", pageToken=response['nextPageToken']
                    )
                else:
                    break
        return comentarios
    except Exception as e:
        st.error(f"Error: {e}")
        return []

# --- INTERFAZ PRINCIPAL ---
url_video = st.text_input("Enlace del video:")
palabra_filtro = st.text_input("Palabra clave (opcional):")

if st.button("Cargar Participantes", type="primary"):
    if not api_key:
        st.warning("Falta la API Key.")
    elif not url_video:
        st.warning("Falta el enlace.")
    else:
        video_id = obtener_id_video(url_video)
        if video_id:
            res = obtener_comentarios(api_key, video_id, palabra_filtro)
            if res:
                st.session_state['participantes'] = res
                st.success(f"¡{len(res)} comentarios cargados!")
            else:
                st.warning("No se encontraron comentarios.")

# --- PROCESO DE SORTEO ---
if 'participantes' in st.session_state:
    if st.button("✨ ¡REALIZAR SORTEO!"):
        participantes = st.session_state['participantes'].copy()
        total_necesario = num_ganadores + num_suplentes
        
        if len(participantes) < total_necesario:
            st.error(f"No hay suficientes participantes. Tienes {len(participantes)} y necesitas {total_necesario}.")
        else:
            random.shuffle(participantes) # Mezclamos la lista
            
            ganadores = participantes[:num_ganadores]
            suplentes = participantes[num_ganadores:total_necesario]
            
            st.balloons()
            
            st.header("🏆 GANADORES")
            for i, g in enumerate(ganadores, 1):
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.subheader(f"{i}. {g['Autor']}")
                        st.write(f"💬 {g['Comentario']}")
                    with col_b:
                        st.link_button("🔗 Ver comentario", g['Link'])
                st.divider()
            
            if suplentes:
                st.header("⏳ SUPLENTES")
                for i, s in enumerate(suplentes, 1):
                    st.write(f"**Suplente {i}:** {s['Autor']}")
                    
