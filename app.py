import streamlit as st
import pandas as pd
from github import Github
import base64
import json
from datetime import datetime
import requests
import time
import hmac

# ============================================
# CONFIGURACIÓN - SIN CACHÉ
# ============================================
st.set_page_config(
    page_title="Sistema Gestión Empleados",
    page_icon="👔",
    layout="wide"
)

# ============================================
# 🔐 SISTEMA DE LOGIN - CONTRASEÑA ÚNICA (OPCIÓN 1)
# ============================================
def check_password():
    """Retorna True si el usuario ingresó la contraseña correcta"""
    
    # Verificar que el secret existe
    if "PASSWORD" not in st.secrets:
        st.error("❌ Error: PASSWORD no configurado en Secrets")
        return False
    
    def password_entered():
        """Verifica la contraseña ingresada"""
        if hmac.compare_digest(st.session_state["password"], st.secrets["PASSWORD"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # No guardar contraseña
        else:
            st.session_state["password_correct"] = False
    
    # Si ya está autenticado, permitir acceso
    if st.session_state.get("password_correct", False):
        return True
    
    # Mostrar formulario de login
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .login-box {
            background: white;
            padding: 2.5rem;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            max-width: 400px;
            margin: 100px auto;
            text-align: center;
        }
        .login-title {
            color: #333;
            margin-bottom: 10px;
        }
        .login-subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor del login
    with st.container():
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # Logo
        st.image("https://img.icons8.com/color/96/000000/employee-card.png", width=100)
        
        # Título
        st.markdown('<h2 class="login-title">🔐 Sistema de Gestión</h2>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Ingrese la contraseña de acceso</p>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Campo de contraseña
        st.text_input(
            "Contraseña",
            type="password",
            key="password",
            on_change=password_entered,
            placeholder="Ingrese la contraseña"
        )
        
        st.markdown("---")
        st.markdown('<p style="color: #999; font-size: 0.8em;">© 2026 - Gestión de Empleados</p>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Mostrar error si la contraseña es incorrecta
    if st.session_state.get("password_correct") == False:
        st.error("❌ Contraseña incorrecta")
    
    return False

# 🔐 VERIFICAR AUTENTICACIÓN ANTES DE MOSTRAR CUALQUIER COSA
if not check_password():
    st.stop()  # Detener ejecución si no está autenticado

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
# INICIALIZACIÓN
# ============================================
if 'ultima_actualizacion' not in st.session_state:
    st.session_state.ultima_actualizacion = datetime.now()
    st.session_state.refresh_count = 0
    st.session_state.ultimo_id_agregado = None
    st.session_state.menu_seleccion = "📋 Ver Empleados"

# ============================================
# FUNCIONES DE GITHUB - SIN CACHÉ CDN
# ============================================
def obtener_empleados():
    """Lee empleados usando RAW + timestamp (NO USA API)"""
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/datos/empleados_actualizado.json?t={int(time.time()*1000)}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            df = pd.read_json(response.text)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def guardar_solicitud(tipo, datos):
    """Guarda solicitud en GitHub - SOLO ESCRITURA USA API"""
    try:
        from github import Github
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
        from github import Github
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
# BARRA SUPERIOR - USUARIO AUTENTICADO
# ============================================
col1, col2, col3 = st.columns([3,1,1])
with col1:
    st.title("👔 SISTEMA DE GESTIÓN DE EMPLEADOS")
with col3:
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.password_correct = False
        st.rerun()

st.markdown("---")

# ============================================
# MENÚ LATERAL
# ============================================
st.sidebar.title("📋 MENÚ PRINCIPAL")

def cambiar_menu():
    st.session_state.menu_seleccion = st.session_state._menu_widget

st.sidebar.radio(
    "Seleccione una opción",
    ["📋 Ver Empleados", "➕ Agregar Empleado", "✏️ Editar Empleado", "🗑️ Eliminar Empleado"],
    key="_menu_widget",
    on_change=cambiar_menu
)

menu = st.session_state.menu_seleccion
st.sidebar.success(f"📁 {GITHUB_REPO}")
st.sidebar.info("🔐 Sesión activa")

# ============================================
# AUTO-REFRESH - SOLO EN VER EMPLEADOS
# ============================================
if menu == "📋 Ver Empleados":
    ahora = datetime.now()
    delta = (ahora - st.session_state.ultima_actualizacion).seconds
    
    col1, col2, col3 = st.columns([1,1,3])
    with col1:
        if st.button("🔄 Recargar", use_container_width=True):
            st.cache_data.clear()
            st.session_state.ultima_actualizacion = datetime.now()
            st.session_state.refresh_count += 1
            st.rerun()
    with col2:
        st.info(f"🔄 #{st.session_state.refresh_count}")
    with col3:
        if delta < 30:
            st.success(f"⏱️ Datos actualizados hace {delta} segundos")
        else:
            st.warning(f"⏱️ Última actualización hace {delta} segundos")
    
    if delta >= 30:
        st.session_state.ultima_actualizacion = ahora
        st.session_state.refresh_count += 1
        st.rerun()

# ============================================
# 1. VER EMPLEADOS
# ============================================
if menu == "📋 Ver Empleados":
    st.header("📋 Lista de Empleados")
    
    with st.spinner("Cargando datos..."):
        df = obtener_empleados()
    
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Empleados", len(df))
        col2.metric("Último ID", df['empleadoId'].max())
        if 'FechaActualizacion' in df.columns:
            col3.metric("Actualización", df['FechaActualizacion'].iloc[0][11:19])
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
        
        if st.session_state.ultimo_id_agregado:
            if st.session_state.ultimo_id_agregado in df['empleadoId'].values:
                st.success(f"✅ Nuevo empleado ID {st.session_state.ultimo_id_agregado} agregado")
                st.session_state.ultimo_id_agregado = None
            else:
                st.info(f"⏳ Procesando ID {st.session_state.ultimo_id_agregado}...")
    else:
        st.warning("No hay empleados registrados")

# ============================================
# 2. AGREGAR EMPLEADO
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
            submitted = st.form_submit_button("💾 Guardar", type="primary", use_container_width=True)
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
                            st.session_state.ultimo_id_agregado = empleadoId
                            time.sleep(1)
                            st.session_state.menu_seleccion = "📋 Ver Empleados"
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
        
        if cancel:
            st.rerun()

# ============================================
# 3. EDITAR EMPLEADO
# ============================================
elif menu == "✏️ Editar Empleado":
    st.header("✏️ Editar Empleado")
    
    df = obtener_empleados()
    
    if not df.empty:
        empleadoId = st.selectbox("Seleccione ID", sorted(df['empleadoId'].tolist()))
        
        if empleadoId:
            empleado = df[df['empleadoId'] == empleadoId].iloc[0]
            
            with st.form("form_editar"):
                nombre = st.text_input("Nombre", value=empleado['Nombre'])
                cargo = st.text_input("Cargo", value=empleado['Cargo'], max_chars=100)
                
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("🔄 Actualizar", type="primary", use_container_width=True)
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
                                st.success(f"✅ Solicitud guardada - ID: {empleadoId}")
                                time.sleep(1)
                                st.session_state.menu_seleccion = "📋 Ver Empleados"
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                    else:
                        st.warning("⚠️ Nombre y Cargo obligatorios")
                
                if cancel:
                    st.rerun()
    else:
        st.info("No hay empleados")

# ============================================
# 4. ELIMINAR EMPLEADO
# ============================================
elif menu == "🗑️ Eliminar Empleado":
    st.header("🗑️ Eliminar Empleado")
    
    df = obtener_empleados()
    
    if not df.empty:
        empleadoId = st.selectbox("Seleccione ID", sorted(df['empleadoId'].tolist()))
        
        if empleadoId:
            empleado = df[df['empleadoId'] == empleadoId].iloc[0]
            
            st.error(f"""
            ### ⚠️ ¿Eliminar?
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
                            st.success(f"✅ Solicitud guardada - ID: {empleadoId}")
                            time.sleep(1)
                            st.session_state.menu_seleccion = "📋 Ver Empleados"
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
            with col2:
                if st.button("❌ No, cancelar", use_container_width=True):
                    st.rerun()
    else:
        st.info("No hay empleados")

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray;'>
    <p>⚡ <strong>SISTEMA SEGURO</strong> - Acceso restringido</p>
    <p>🔄 Última recarga: {datetime.now().strftime('%H:%M:%S')}</p>
    <p>🔐 Sesión activa - Usuario autorizado</p>
</div>
""", unsafe_allow_html=True)
