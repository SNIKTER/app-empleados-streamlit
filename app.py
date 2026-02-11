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
# FUNCIONES DE GITHUB
# ============================================
@st.cache_data(ttl=0)  # Sin caché
def obtener_empleados():
    """Lee empleados desde GitHub RAW"""
    try:
        url = "https://raw.githubusercontent.com/SNIKTER/datos-empleados-privado/main/datos/empleados_actualizado.json"
        headers = {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            df = pd.read_json(response.text)
            return df
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

def guardar_solicitud(tipo, datos):
    """Guarda solicitud en GitHub"""
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        
        # Leer solicitudes existentes
        try:
            contents = repo.get_contents("solicitudes/solicitudes_pendientes.json")
            solicitudes = json.loads(base64.b64decode(contents.content).decode('utf-8'))
        except:
            solicitudes = []
        
        # Crear nueva solicitud
        nueva = {
            "id": len(solicitudes) + 1,
            "tipo": tipo,
            "datos": datos,
            "fecha_solicitud": datetime.now().isoformat(),
            "estado": "pendiente"
        }
        solicitudes.append(nueva)
        
        # Guardar en GitHub
        if 'contents' in locals():
            repo.update_file(
                "solicitudes/solicitudes_pendientes.json",
                f"{tipo} - {datos.get('empleadoId', '')}",
                json.dumps(solicitudes, indent=2),
                contents.sha
            )
        else:
            repo.create_file(
                "solicitudes/solicitudes_pendientes.json",
                "Inicialización",
                json.dumps(solicitudes, indent=2)
            )
        
        return True, "✅ Solicitud guardada"
    except Exception as e:
        return False, str(e)

def obtener_solicitudes_pendientes():
    """Lee solicitudes pendientes para validación"""
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        contents = repo.get_contents("solicitudes/solicitudes_pendientes.json")
        solicitudes = json.loads(base64.b64decode(contents.content).decode('utf-8'))
        return [s for s in solicitudes if s.get('estado') == 'pendiente']
    except:
        return []

def verificar_id_disponible(df, empleadoId, solicitudes_pendientes):
    """Verifica si un ID está disponible"""
    if df.empty:
        return True
    if empleadoId in df['empleadoId'].values:
        return False
    for sol in solicitudes_pendientes:
        if sol['tipo'] == 'INSERT' and sol['datos'].get('empleadoId') == empleadoId:
            return False
    return True

# ============================================
# AUTO-REFRESH CADA 2 SEGUNDOS
# ============================================
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()
    st.session_state.refresh_count = 0

now = datetime.now()
delta = (now - st.session_state.last_refresh).seconds

if delta >= 2:
    st.session_state.last_refresh = now
    st.session_state.refresh_count += 1
    st.rerun()

# ============================================
# BARRA LATERAL - MENÚ
# ============================================
st.sidebar.title("📋 MENÚ PRINCIPAL")
st.sidebar.markdown("---")

menu = st.sidebar.selectbox(
    "Seleccione una opción",
    ["📋 Ver Empleados", "➕ Agregar Empleado", "✏️ Editar Empleado", "🗑️ Eliminar Empleado"]
)

st.sidebar.markdown("---")
st.sidebar.info(f"🔄 Auto-refresh cada 2 segundos\n#{st.session_state.refresh_count}")

# ============================================
# 1. VER EMPLEADOS
# ============================================
if menu == "📋 Ver Empleados":
    st.header("📋 Lista de Empleados")
    
    col1, col2 = st.columns([1,5])
    with col1:
        if st.button("🔄 Recargar ahora", use_container_width=True):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
    
    df = obtener_empleados()
    
    if not df.empty:
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Empleados", len(df))
        with col2:
            st.metric("Último ID", df['empleadoId'].max())
        with col3:
            if 'FechaActualizacion' in df.columns:
                hora = df['FechaActualizacion'].iloc[0][11:19]
                st.metric("Actualización SQL", hora)
        with col4:
            st.metric("Cargos distintos", df['Cargo'].nunique())
        
        # Tabla
        st.dataframe(
            df[['empleadoId', 'Nombre', 'Cargo']].sort_values('empleadoId'),
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Botón descarga
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
# 2. AGREGAR EMPLEADO
# ============================================
elif menu == "➕ Agregar Empleado":
    st.header("➕ Agregar Nuevo Empleado")
    
    # Cargar datos actuales
    df = obtener_empleados()
    solicitudes_pendientes = obtener_solicitudes_pendientes()
    
    with st.form("form_agregar", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            empleadoId = st.number_input("🆔 ID del Empleado *", min_value=1, step=1)
        with col2:
            nombre = st.text_input("👤 Nombre Completo *")
        
        cargo = st.text_input("💼 Cargo *", max_chars=100)
        st.caption(f"Máximo 100 caracteres: {len(cargo)}/100")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Guardar Empleado", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("🧹 Limpiar", use_container_width=True)
        
        if submit:
            if empleadoId and nombre and cargo:
                # Validar ID disponible
                if not verificar_id_disponible(df, empleadoId, solicitudes_pendientes):
                    st.error(f"❌ El ID {empleadoId} ya existe en la base de datos o está pendiente")
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
                            st.info("🔄 Los cambios se verán en 1-2 segundos")
                            st.balloons()
                        else:
                            st.error(f"❌ Error: {msg}")
            else:
                st.warning("⚠️ Todos los campos son obligatorios")

# ============================================
# 3. EDITAR EMPLEADO
# ============================================
elif menu == "✏️ Editar Empleado":
    st.header("✏️ Editar Empleado")
    
    df = obtener_empleados()
    
    if not df.empty:
        empleadoId = st.selectbox(
            "Seleccione ID del empleado a editar",
            sorted(df['empleadoId'].tolist())
        )
        
        if empleadoId:
            empleado = df[df['empleadoId'] == empleadoId].iloc[0]
            
            with st.form("form_editar"):
                nombre = st.text_input("Nombre", value=empleado['Nombre'])
                cargo = st.text_input("Cargo", value=empleado['Cargo'], max_chars=100)
                
                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("🔄 Actualizar", type="primary", use_container_width=True)
                with col2:
                    cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
                
                if submit:
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
                                st.info("🔄 Los cambios se verán en 1-2 segundos")
                            else:
                                st.error(f"❌ Error: {msg}")
                    else:
                        st.warning("⚠️ Nombre y Cargo son obligatorios")
    else:
        st.info("No hay empleados para editar")

# ============================================
# 4. ELIMINAR EMPLEADO
# ============================================
elif menu == "🗑️ Eliminar Empleado":
    st.header("🗑️ Eliminar Empleado")
    
    df = obtener_empleados()
    
    if not df.empty:
        empleadoId = st.selectbox(
            "Seleccione ID del empleado a eliminar",
            sorted(df['empleadoId'].tolist())
        )
        
        if empleadoId:
            empleado = df[df['empleadoId'] == empleadoId].iloc[0]
            
            st.warning(f"""
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
                            st.info("🔄 Los cambios se verán en 1-2 segundos")
                        else:
                            st.error(f"❌ Error: {msg}")
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
    <p>⚡ <strong>TIEMPO REAL</strong> - Actualización automática cada 2 segundos</p>
    <p>🔄 Los cambios se reflejan en menos de 3 segundos</p>
</div>
""", unsafe_allow_html=True)
