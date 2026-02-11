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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# INICIALIZACIÓN
# ============================================
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# ============================================
# 🔐 LOGIN - 100% FUNCIONAL
# ============================================
def check_password():
    if st.session_state.get("autenticado", False):
        return True
    
    st.title("🔐 Sistema de Gestión de Empleados")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://img.icons8.com/color/96/000000/employee-card.png", width=120)
        st.markdown("## Acceso al sistema")
        st.markdown("### FINANZAUTO S.A. BIC")
        st.markdown("---")
        
        password = st.text_input(
            "Contraseña",
            type="password",
            key="password_input",
            placeholder="Ingrese su contraseña"
        )
        
        if st.button("Ingresar", type="primary", use_container_width=True):
            if "PASSWORD" in st.secrets:
                if hmac.compare_digest(password, st.secrets["PASSWORD"]):
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
            else:
                st.error("❌ Error: PASSWORD no configurado en Secrets")
        
        st.markdown("---")
        st.caption("© 2026 FINANZAUTO S.A. BIC")
    
    return False

# 🔐 VERIFICAR AUTENTICACIÓN
if not check_password():
    st.stop()

# ============================================
# 🚀 APLICACIÓN PRINCIPAL (SOLO SI ESTÁ AUTENTICADO)
# ============================================
st.success("✅ ¡Bienvenido! Has iniciado sesión correctamente.")
st.write("Aquí va tu aplicación de gestión de empleados...")

# Botón para cerrar sesión
if st.sidebar.button("🚪 Cerrar sesión"):
    st.session_state.autenticado = False
    st.rerun()
# ============================================
# 🔐 VERIFICAR AUTENTICACIÓN
# ============================================
if not check_password():
    st.stop()

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
# BARRA SUPERIOR - HEADER CORPORATIVO
# ============================================
st.markdown("""
<style>
    /* Header corporativo */
    .corporate-header {
        background: white;
        padding: 16px 24px;
        border-bottom: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }
    
    .corporate-title {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .corporate-title h1 {
        font-size: 20px;
        font-weight: 600;
        color: #0a1e3c;
        margin: 0;
    }
    
    .corporate-badge {
        background: #f1f5f9;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 12px;
        color: #0a1e3c;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .logout-btn {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 8px 16px;
        color: #64748b;
        font-size: 14px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .logout-btn:hover {
        background: #f8fafc;
        border-color: #94a3b8;
    }
</style>

<div class="corporate-header">
    <div class="corporate-title">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#0a1e3c" stroke-width="1.5">
            <path d="M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12Z"/>
            <path d="M20 21V19C20 16.8 18.2 15 16 15H8C5.8 15 4 16.8 4 19V21"/>
        </svg>
        <h1>Sistema de Gestión de Empleados</h1>
    </div>
    <div style="display: flex; align-items: center; gap: 16px;">
        <div class="corporate-badge">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0a1e3c" stroke-width="2">
                <circle cx="12" cy="8" r="4"/>
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
            </svg>
            <span>SESIÓN ACTIVA</span>
        </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1,1])
with col1:
    if st.button("🚪 Cerrar Sesión", key="logout_btn"):
        st.session_state.password_correct = False
        st.rerun()

st.markdown("</div></div>", unsafe_allow_html=True)

# ============================================
# MENÚ LATERAL - CORPORATIVO
# ============================================
st.sidebar.markdown("""
<style>
    .sidebar-brand {
        padding: 24px 16px;
        margin-bottom: 16px;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .sidebar-brand h3 {
        color: #0a1e3c;
        font-size: 16px;
        font-weight: 600;
        margin: 0;
    }
    
    .sidebar-brand p {
        color: #64748b;
        font-size: 12px;
        margin: 4px 0 0 0;
    }
    
    .sidebar-footer {
        position: fixed;
        bottom: 0;
        padding: 24px 16px;
        font-size: 11px;
        color: #94a3b8;
    }
</style>

<div class="sidebar-brand">
    <h3>FINANZAUTO S.A. BIC</h3>
    <p>Gestión de Talento Humano</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("📋 Menú Principal")

def cambiar_menu():
    st.session_state.menu_seleccion = st.session_state._menu_widget

st.sidebar.radio(
    "Opciones",
    ["📋 Ver Empleados", "➕ Agregar Empleado", "✏️ Editar Empleado", "🗑️ Eliminar Empleado"],
    key="_menu_widget",
    on_change=cambiar_menu,
    label_visibility="collapsed"
)

st.sidebar.markdown(f"""
<div class="sidebar-footer">
    <div style="margin-bottom: 8px;">📁 {GITHUB_REPO}</div>
    <div>🕐 {datetime.now().strftime('%H:%M:%S')}</div>
    <div style="margin-top: 16px;">© 2026 v2.0.1</div>
</div>
""", unsafe_allow_html=True)

menu = st.session_state.menu_seleccion

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
        return pd.DataFrame()
    except:
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
# AUTO-REFRESH - SOLO EN VER EMPLEADOS
# ============================================
if menu == "📋 Ver Empleados":
    ahora = datetime.now()
    delta = (ahora - st.session_state.ultima_actualizacion).seconds
    
    col1, col2, col3 = st.columns([1,1,4])
    with col1:
        if st.button("🔄 Recargar", use_container_width=True):
            st.cache_data.clear()
            st.session_state.ultima_actualizacion = datetime.now()
            st.session_state.refresh_count += 1
            st.rerun()
    with col2:
        st.info(f"#{st.session_state.refresh_count}")
    with col3:
        if delta < 30:
            st.caption(f"✅ Datos actualizados hace {delta} segundos")
    
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
            ### ⚠️ ¿Eliminar este empleado?
            
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



