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
# 🔐 LOGIN CORPORATIVO PROFESIONAL - CORREGIDO
# ============================================
def check_password():
    """Diseño corporativo profesional - limpio y elegante"""
    
    if "PASSWORD" not in st.secrets:
        st.error("❌ Error: PASSWORD no configurado en Secrets")
        return False
    
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["PASSWORD"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    
    if st.session_state.get("password_correct", False):
        return True
    
    # CSS Corporativo Profesional
    st.markdown("""
    <style>
        /* RESET Y BASE */
        .stApp {
            background-color: #ffffff;
        }
        
        /* Eliminar padding y márgenes por defecto */
        .main > div {
            padding: 0 !important;
        }
        
        /* Ocultar elementos por defecto */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Contenedor principal */
        .login-wrapper {
            display: flex;
            min-height: 100vh;
            width: 100%;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            z-index: 999999;
            background: white;
        }
        
        /* Panel izquierdo - Branding */
        .brand-panel {
            flex: 1;
            background: linear-gradient(165deg, #0a1e3c 0%, #0b2c4a 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 40px;
            position: relative;
            overflow: hidden;
        }
        
        .brand-panel::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="none"/><path d="M0 0 L100 100 M100 0 L0 100" stroke="rgba(255,255,255,0.03)" stroke-width="1"/></svg>');
            opacity: 0.4;
        }
        
        .brand-content {
            position: relative;
            z-index: 2;
            max-width: 400px;
            color: white;
        }
        
        .brand-icon {
            width: 64px;
            height: 64px;
            background: rgba(255,255,255,0.1);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 32px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .brand-title {
            font-size: 32px;
            font-weight: 600;
            margin-bottom: 16px;
            letter-spacing: -0.5px;
            line-height: 1.2;
        }
        
        .brand-subtitle {
            font-size: 16px;
            opacity: 0.8;
            margin-bottom: 48px;
            line-height: 1.6;
        }
        
        .brand-feature {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            font-size: 15px;
            opacity: 0.9;
        }
        
        .brand-feature svg {
            flex-shrink: 0;
        }
        
        /* Panel derecho - Login */
        .login-panel {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px;
            background-color: white;
        }
        
        .login-card {
            width: 100%;
            max-width: 360px;
        }
        
        .login-header {
            margin-bottom: 40px;
        }
        
        .login-header h2 {
            font-size: 24px;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
            letter-spacing: -0.3px;
        }
        
        .login-header p {
            font-size: 14px;
            color: #64748b;
        }
        
        /* Input personalizado */
        .stTextInput > div {
            margin-bottom: 24px;
        }
        
        .stTextInput > div > div {
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            transition: all 0.2s;
        }
        
        .stTextInput > div > div:hover {
            border-color: #94a3b8;
        }
        
        .stTextInput > div > div:focus-within {
            border-color: #2563eb;
            box-shadow: 0 0 0 4px rgba(37,99,235,0.1);
        }
        
        .stTextInput input {
            padding: 12px 16px !important;
            font-size: 15px !important;
        }
        
        /* Botón */
        .stButton > button {
            background: #0a1e3c;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 15px;
            font-weight: 500;
            width: 100%;
            transition: all 0.2s;
            margin-top: 8px;
        }
        
        .stButton > button:hover {
            background: #0b2c4a;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(10,30,60,0.15);
        }
        
        /* Mensaje de error */
        .stAlert {
            border-radius: 8px;
            border-left: 4px solid #dc2626;
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999999;
            width: 400px;
        }
        
        /* Footer */
        .login-footer {
            margin-top: 48px;
            text-align: center;
            color: #94a3b8;
            font-size: 13px;
        }
        
        .login-footer span {
            color: #0a1e3c;
            font-weight: 500;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .login-wrapper {
                flex-direction: column;
                position: relative;
            }
            
            .brand-panel {
                padding: 60px 24px;
            }
            
            .brand-content {
                text-align: center;
            }
            
            .brand-icon {
                margin: 0 auto 32px auto;
            }
            
            .brand-feature {
                justify-content: center;
            }
            
            .stAlert {
                width: 90%;
                left: 5%;
                right: 5%;
            }
        }
    </style>
    
    <div class="login-wrapper">
        <!-- Panel Izquierdo - Branding -->
        <div class="brand-panel">
            <div class="brand-content">
                <div class="brand-icon">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.5">
                        <path d="M12 12C14.21 12 16 10.21 16 8C16 5.79 14.21 4 12 4C9.79 4 8 5.79 8 8C8 10.21 9.79 12 12 12Z"/>
                        <path d="M20 21V19C20 16.8 18.2 15 16 15H8C5.8 15 4 16.8 4 19V21"/>
                    </svg>
                </div>
                <div class="brand-title">Sistema de Gestión<br>de Empleados</div>
                <div class="brand-subtitle">Plataforma integral para la administración del talento humano</div>
                
                <div class="brand-feature">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                        <path d="M20 6L9 17L4 12" stroke="white" stroke-width="2"/>
                    </svg>
                    <span>Gestión en tiempo real</span>
                </div>
                <div class="brand-feature">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                        <path d="M20 6L9 17L4 12" stroke="white" stroke-width="2"/>
                    </svg>
                    <span>Actualización automática</span>
                </div>
                <div class="brand-feature">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                        <path d="M20 6L9 17L4 12" stroke="white" stroke-width="2"/>
                    </svg>
                    <span>Acceso seguro y controlado</span>
                </div>
            </div>
        </div>
        
        <!-- Panel Derecho - Login -->
        <div class="login-panel">
            <div class="login-card">
                <div class="login-header">
                    <h2>Acceso al sistema</h2>
                    <p>Ingrese sus credenciales para continuar</p>
                </div>
    """, unsafe_allow_html=True)
    
    # Campo de contraseña - ESTO DEBE ESTAR FUERA DEL st.markdown
    password = st.text_input(
        "Contraseña de acceso",
        type="password",
        key="password",
        placeholder="••••••••",
        label_visibility="collapsed"
    )
    
    # Botón de acceso - Streamlit nativo
    if st.button("Iniciar sesión", type="primary", use_container_width=True):
        password_entered()
    
    # Footer
    st.markdown("""
                <div class="login-footer">
                    <p>© 2026 FINANZAUTO S.A. BIC</p>
                    <p style="margin-top: 8px;">Todos los derechos reservados · <span>v2.0.1</span></p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.get("password_correct") == False:
        st.error("❌ La contraseña ingresada no es correcta")
    
    return False

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

