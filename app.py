import streamlit as st
import pandas as pd
from github import Github
import base64
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="Sistema Gestión Empleados",
    page_icon="👔",
    layout="wide"
)

# ============================================
# TÍTULO
# ============================================
st.title("👔 SISTEMA DE GESTIÓN DE EMPLEADOS")
st.markdown("---")

# ============================================
# FUNCIÓN PARA CARGAR DATOS DESDE GITHUB
# ============================================
@st.cache_data(ttl=300)
def cargar_datos():
    try:
        # Estos valores se configurarán en Streamlit Cloud Secrets
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        contents = repo.get_contents(st.secrets["GITHUB_PATH"])
        
        json_content = base64.b64decode(contents.content).decode('utf-8')
        df = pd.read_json(json_content)
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return pd.DataFrame()

# ============================================
# BARRA LATERAL
# ============================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/employee-card.png", width=80)
    st.markdown("## 👔 Sistema Autorizado")
    st.markdown("---")
    st.markdown("**Uso exclusivo:** Personal de Gestión Humana")
    
    if st.button("🔄 Recargar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ============================================
# CARGA DE DATOS
# ============================================
with st.spinner("Cargando datos actualizados..."):
    df = cargar_datos()

# ============================================
# MOSTRAR DATOS
# ============================================
if not df.empty:
    # Métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Total Empleados", f"{len(df):,}")
    with col2:
        if 'FechaActualizacion' in df.columns:
            ultima_fecha = df['FechaActualizacion'].iloc[0][:10]
            st.metric("🕐 Última actualización", ultima_fecha)
    with col3:
        st.metric("🏢 Cargos distintos", df['Cargo'].nunique())
    
    st.markdown("---")
    
    # Tabla de empleados
    st.subheader("📋 Listado de Empleados")
    
    columnas_mostrar = ['empleadoId', 'Nombre', 'Cargo']
    if all(col in df.columns for col in columnas_mostrar):
        st.dataframe(
            df[columnas_mostrar],
            use_container_width=True,
            hide_index=True,
            column_config={
                "empleadoId": st.column_config.NumberColumn("ID"),
                "Nombre": st.column_config.TextColumn("Nombre Completo"),
                "Cargo": st.column_config.TextColumn("Cargo")
            }
        )
    else:
        st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    
    # Botón de descarga
    csv = df.to_csv(index=False, encoding='utf-8')
    st.download_button(
        label="📥 DESCARGAR EXCEL",
        data=csv,
        file_name=f"empleados_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
else:
    st.error("""
    ❌ **No se pudieron cargar los datos**
    
    Contacte al administrador del sistema.
    """)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🔒 Sistema de uso interno - Datos actualizados automáticamente</p>
</div>
""", unsafe_allow_html=True)