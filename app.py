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
# VERIFICAR SECRETS
# ============================================
if "GITHUB_TOKEN" not in st.secrets:
    st.error("❌ Error: GITHUB_TOKEN no configurado en Secrets")
    st.stop()
if "GITHUB_REPO" not in st.secrets:
    st.error("❌ Error: GITHUB_REPO no configurado en Secrets")
    st.stop()

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

# ============================================
# FUNCIONES DE GITHUB
# ============================================
@st.cache_data(ttl=2)
def obtener_empleados():
    """Lee empleados desde GitHub RAW"""
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/datos/empleados_actualizado.json"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            df = pd.read_json(response.text)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def guardar_solicitud(tipo, datos):
    """Guarda solicitud en GitHub"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        try:
            contents = repo.get_contents("solicitudes/solicitudes_pendientes.json")
            solicitudes = json.loads(base64.b64decode(contents.content).decode('utf-8'))
        except:
            solicitudes = []
        
        nueva = {
            "id": len(solicitudes) + 1,
            "tipo": tipo,
            "datos": datos,
            "fecha_solicitud": datetime.now().isoformat(),
            "estado": "pendiente"
        }
        solicitudes.append(nueva)
        
        json_data = json.dumps(solicitudes, indent=2, ensure_ascii=False)
        
        try:
            repo.update_file(
                "solicitudes/solicitudes_pendientes.json",
                f"{tipo} - ID: {datos.get('empleadoId', '')} - {datetime.now().strftime('%H:%M:%S')}",
                json_data,
                contents.sha
            )
        except:
            repo.create_file(
                "solicitudes/solicitudes_pendientes.json",
                f"Creación - {datetime.now().strftime('%H:%M:%S')}",
                json_data
            )
        
        return True, "✅ Solicitud guardada correctamente"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def obtener_solicitudes_pendientes():
    """Lee solicitudes pendientes"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        try:
            contents = repo.get_contents("solicitudes/solicitudes_pendientes.json")
            solicitudes = json.loads(base64.b64decode(contents.content).decode('utf-8'))
            return [s for s in solicitudes if s.get('estado') == 'pendiente']
        except:
            return []
    except:
        return []

def verificar_id_disponible(df, empleadoId, solicitudes_pendientes):
    """Verifica si un ID está disponible"""
    if df is not None and not df.empty:
        if empleadoId in df['empleadoId'].values:
            return False, f"❌ El ID {empleadoId} ya existe en la base de datos"
    
    for sol in solicitudes_pendientes:
        if sol['tipo'] == 'INSERT' and sol['datos'].get('empleadoId') == empleadoId:
            return False, f"❌ El ID {empleadoId} ya tiene una solicitud pendiente"
    
    return True, "✅ ID disponible"

# ============================================
# AUTO-REFRESH - SOLO EN VER EMPLEADOS
# ============================================
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
    st.session_state.refresh_count = 0
    st.session_state.ultimo_menu = "📋 Ver Empleados"

# ============================================
# MENÚ LATERAL
# ============================================
st.sidebar.title("📋 MENÚ PRINCIPAL")
menu = st.sidebar.selectbox(
    "Seleccione una opción",
    ["📋 Ver Empleados", "➕ Agregar Empleado", "✏️ Editar Empleado", "🗑️ Eliminar Empleado"]
)

# Control de auto-refresh por menú
if menu == "📋 Ver Empleados":
    now = datetime.now()
    delta = (now - st.session_state.last_refresh).seconds
    if delta >= 5:
        st.session_state.last_refresh = now
        st.session_state.refresh_count += 1
        st.rerun()
    st.sidebar.info(f"🔄 Auto-refresh cada 5 segundos\n#{st.session_state.refresh_count}")
else:
    st.sidebar.info(f"⏸️ Auto-refresh desactivado - Modo edición")

st.sidebar.success(f"📁 {GITHUB_REPO}")

# ============================================
# 1. VER EMPLEADOS
# ============================================
if menu == "📋 Ver Empleados":
    st.header("📋 Lista de Empleados")
    
    col1, col2 = st.columns([1,5])
    with col1:
        if st.button("🔄 Recargar ahora", use_container_width=True):
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    df = obtener_empleados()
    
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Empleados", len(df))
        col2.metric("Último ID", df['empleadoId'].max())
        if 'FechaActualizacion' in df.columns:
            col3.metric("Actualización SQL", df['FechaActualizacion'].iloc[0][11:19])
        col4.metric("Cargos distintos", df['Cargo'].nunique())
        
        st.dataframe(
            df[['empleadoId', 'Nombre', 'Cargo']].sort_values('empleadoId'),
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar Excel",
            csv,
            f"empleados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            use_container_width=True
        )
    else:
        st.warning("No hay empleados registrados")

# ============================================
# 2. AGREGAR EMPLEADO - SIN AUTO-REFRESH
# ============================================
elif menu == "➕ Agregar Empleado":
    st.header("➕ Agregar Nuevo Empleado")
    
    df = obtener_empleados()
    solicitudes_pendientes = obtener_solicitudes_pendientes()
    
    with st.form("form_agregar"):
        empleadoId = st.number_input("🆔 ID del Empleado *", min_value=1, step=1, value=1)
        nombre = st.text_input("👤 Nombre Completo *")
        cargo = st.text_input("💼 Cargo *", max_chars=100)
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Guardar Empleado", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("🧹 Limpiar", use_container_width=True)
        
        if submitted:
            if not empleadoId or not nombre or not cargo:
                st.error("⚠️ Todos los campos son obligatorios")
            else:
                disponible, mensaje = verificar_id_disponible(df, empleadoId, solicitudes_pendientes)
                if not disponible:
                    st.error(mensaje)
                else:
                    with st.spinner("Guardando solicitud..."):
                        datos = {
                            "empleadoId": int(empleadoId),
                            "Nombre": nombre.strip(),
                            "Cargo": cargo.strip()
                        }
                        success, msg = guardar_solicitud("INSERT", datos)
                        
                        if success:
                            st.success(f"✅ Solicitud guardada - ID: {empleadoId}")
                            st.balloons()
                        else:
                            st.error(f"❌ {msg}")
        
        if cancel:
            st.rerun()

# ============================================
# 3. EDITAR EMPLEADO - SIN AUTO-REFRESH
# ============================================
elif menu == "✏️ Editar Empleado":
    st.header("✏️ Editar Empleado")
    
    df = obtener_empleados()
    
    if not df.empty:
        empleadoId = st.selectbox("Seleccione ID del empleado a editar", sorted(df['empleadoId'].tolist()))
        
        if empleadoId:
            empleado = df[df['empleadoId'] == empleadoId].iloc[0]
            
            with st.form("form_editar"):
                nombre = st.text_input("Nombre", value=empleado['Nombre'])
                cargo = st.text_input("Cargo", value=empleado['Cargo'], max_chars=100)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("🔄 Actualizar Empleado", type="primary", use_container_width=True)
                with col2:
                    cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
                
                if submitted:
                    if nombre and cargo:
                        with st.spinner("Guardando solicitud..."):
                            datos = {
                                "empleadoId": int(empleadoId),
                                "Nombre": nombre.strip(),
                                "Cargo": cargo.strip()
                            }
                            success, msg = guardar_solicitud("UPDATE", datos)
                            
                            if success:
                                st.success(f"✅ Solicitud de actualización guardada - ID: {empleadoId}")
                            else:
                                st.error(f"❌ {msg}")
                    else:
                        st.warning("⚠️ Nombre y Cargo son obligatorios")
                
                if cancel:
                    st.rerun()
    else:
        st.info("No hay empleados para editar")

# ============================================
# 4. ELIMINAR EMPLEADO - SIN AUTO-REFRESH
# ============================================
elif menu == "🗑️ Eliminar Empleado":
    st.header("🗑️ Eliminar Empleado")
    
    df = obtener_empleados()
    
    if not df.empty:
        empleadoId = st.selectbox("Seleccione ID del empleado a eliminar", sorted(df['empleadoId'].tolist()))
        
        if empleadoId:
            empleado = df[df['empleadoId'] == empleadoId].iloc[0]
            
            st.error(f"""
            ### ⚠️ ¿Está seguro de eliminar este empleado?
            
            **ID:** {empleado['empleadoId']}  
            **Nombre:** {empleado['Nombre']}  
            **Cargo:** {empleado['Cargo']}
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Sí, eliminar", type="primary", use_container_width=True):
                    with st.spinner("Guardando solicitud..."):
                        datos = {"empleadoId": int(empleadoId)}
                        success, msg = guardar_solicitud("DELETE", datos)
                        
                        if success:
                            st.success(f"✅ Solicitud de eliminación guardada - ID: {empleadoId}")
                        else:
                            st.error(f"❌ {msg}")
            with col2:
                if st.button("❌ No, cancelar", use_container_width=True):
                    st.rerun()
    else:
        st.info("No hay empleados para eliminar")

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>⚡ <strong>TIEMPO REAL</strong> - Auto-refresh solo en Ver Empleados</p>
    <p>✅ Modo edición SIN recargas automáticas</p>
</div>
""", unsafe_allow_html=True)
