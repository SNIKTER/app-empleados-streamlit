import streamlit as st
import pandas as pd
from github import Github
import base64
import json
from datetime import datetime
import requests

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(
    page_title="Sistema Gestión Empleados",
    page_icon="👔",
    layout="wide"
)

st.title("👔 SISTEMA DE GESTIÓN DE EMPLEADOS")
st.markdown("---")

# ============================================
# LEER DATOS DIRECTAMENTE (SIN CACHÉ)
# ============================================
def obtener_empleados():
    """Lee datos USANDO RAW URL (más rápido)"""
    try:
        # URL directa al archivo RAW de GitHub
        url = "https://raw.githubusercontent.com/SNIKTER/datos-empleados-privado/main/datos/empleados_actualizado.json"
        
        # Headers con token para repositorio privado
        headers = {
            "Authorization": f"token {st.secrets['GITHUB_TOKEN']}"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            df = pd.read_json(response.text)
            return df
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# ============================================
# AUTO-REFRESH CADA 1 SEGUNDO
# ============================================
refresh_interval = 1  # segundos

# Usar session state para controlar el tiempo
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
    st.session_state.refresh_count = 0

# Calcular si debe refrescar
now = datetime.now()
delta = (now - st.session_state.last_refresh).seconds

if delta >= refresh_interval:
    st.session_state.last_refresh = now
    st.session_state.refresh_count += 1
    st.rerun()

# ============================================
# INTERFAZ DE USUARIO
# ============================================
col1, col2, col3 = st.columns([2,1,1])
with col1:
    st.write(f"⚡ **TIEMPO REAL** - Actualizando cada {refresh_interval} segundo")
with col2:
    st.write(f"🔄 #{st.session_state.refresh_count}")
with col3:
    if st.button("⟳ Ahora"):
        st.session_state.last_refresh = datetime.now()
        st.rerun()

st.markdown("---")

# Cargar datos
with st.spinner("Cargando..."):
    df = obtener_empleados()

if not df.empty:
    # Mostrar hora exacta
    ahora = datetime.now().strftime("%H:%M:%S")
    st.success(f"✅ Datos actualizados: {ahora}")
    
    # Tabla
    st.dataframe(
        df[['empleadoId', 'Nombre', 'Cargo']].sort_values('empleadoId'),
        use_container_width=True,
        height=400
    )
    
    # Métricas en tiempo real
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Empleados", len(df))
    with col2:
        if 'FechaActualizacion' in df.columns:
            ultima = df['FechaActualizacion'].iloc[0][11:19]
            st.metric("Última actualización SQL", ultima)
    with col3:
        st.metric("IDs disponibles", f"{df['empleadoId'].max() + 1} en adelante")
    
    # Botón descarga
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Descargar Excel",
        csv,
        f"empleados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
else:
    st.error("❌ No se pudieron cargar los datos")
