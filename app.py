import streamlit as st
import pandas as pd
from github import Github
import base64
import json
from datetime import datetime
import requests
import time

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

# =========================================
# INICIALIZACIÓN - ESTADO
# ============================================
if 'ultima_actualizacion' not in st.session_state:
    st.session_state.ultima_actualizacion = datetime.now()
    st.session_state.refresh_count = 0
    st.session_state.ultimo_id_agregado = None
    st.session_state.menu_seleccion = "📋 Ver Empleados"
    # 🔴 ESTA ES LA LÍNEA QUE FALTABA:
    st.session_state.ultimo_commit = None
    st.session_state.forzar_recarga = False
# ============================================
# FUNCIÓN PRINCIPAL - SIN CDN CACHÉ
# ============================================
def obtener_empleados():
    """Lee empleados usando API de GitHub - SIN CACHÉ CDN"""
    try:
        # 🔴 USAR API DIRECTA - SIN CDN
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        # Obtener el archivo directamente
        contents = repo.get_contents("datos/empleados_actualizado.json")
        
        # Guardar SHA del commit para detectar cambios
        if st.session_state.ultimo_commit != contents.sha:
            st.session_state.ultimo_commit = contents.sha
            print(f"📦 Nuevo commit detectado: {contents.sha[:7]}")
        
        # Decodificar y convertir a DataFrame
        json_content = base64.b64decode(contents.content).decode('utf-8')
        df = pd.read_json(json_content)
        
        return df
    except Exception as e:
        st.error(f"❌ Error API: {str(e)}")
        
        # FALLBACK: Intentar con RAW + timestamp
        try:
            url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/datos/empleados_actualizado.json?t={int(time.time()*1000)}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                df = pd.read_json(response.text)
                return df
        except:
            pass
        
        return pd.DataFrame()

# ============================================
# FUNCIONES DE ESCRITURA
# ============================================
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
        
        return True, "✅ Solicitud guardada"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def obtener_solicitudes_pendientes():
    """Lee solicitudes pendientes usando API"""
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
            return False, f"❌ El ID {empleadoId} ya existe"
    
    for sol in solicitudes_pendientes:
        if sol['tipo'] == 'INSERT' and sol['datos'].get('empleadoId') == empleadoId:
            return False, f"❌ El ID {empleadoId} ya tiene solicitud pendiente"
    
    return True, "✅ ID disponible"

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

# ============================================
# AUTO-REFRESH INTELIGENTE
# ============================================
if menu == "📋 Ver Empleados":
    ahora = datetime.now()
    delta = (ahora - st.session_state.ultima_actualizacion).seconds
    
    col1, col2, col3 = st.columns([1,1,3])
    with col1:
        if st.button("🔄 Recargar", use_container_width=True):
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
    
    # 🔴 AUTO-REFRESH CADA 10 SEGUNDOS (menos agresivo)
    if delta >= 10:
        st.session_state.ultima_actualizacion = ahora
        st.session_state.refresh_count += 1
        st.rerun()

# ============================================
# 1. VER EMPLEADOS - CON API (SIN CACHÉ)
# ============================================
if menu == "📋 Ver Empleados":
    st.header("📋 Lista de Empleados")
    
    # 🔴 LEER CON API - RESPUESTA INMEDIATA
    with st.spinner("Cargando datos..."):
        df = obtener_empleados()
    
    if not df.empty:
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Empleados", len(df))
        col2.metric("Último ID", df['empleadoId'].max())
        if 'FechaActualizacion' in df.columns:
            col3.metric("Actualización", df['FechaActualizacion'].iloc[0][11:19])
        col4.metric("Cargos distintos", df['Cargo'].nunique())
        
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
            f"empleados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        # Mensaje de nuevo empleado
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
                            
                            # 🔴 REDIRIGIR Y FORZAR RECARGA
                            time.sleep(1)
                            st.session_state.menu_seleccion = "📋 Ver Empleados"
                            st.session_state.ultima_actualizacion = datetime.now()
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
                                st.session_state.ultima_actualizacion = datetime.now()
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
                if st.button("🗑️ Sí", type="primary", use_container_width=True):
                    with st.spinner("Guardando solicitud..."):
                        datos = {"empleadoId": int(empleadoId)}
                        success, msg = guardar_solicitud("DELETE", datos)
                        
                        if success:
                            st.success(f"✅ Solicitud guardada - ID: {empleadoId}")
                            time.sleep(1)
                            st.session_state.menu_seleccion = "📋 Ver Empleados"
                            st.session_state.ultima_actualizacion = datetime.now()
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
            with col2:
                if st.button("❌ No", use_container_width=True):
                    st.rerun()
    else:
        st.info("No hay empleados")

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: gray;'>
    <p>⚡ <strong>SIN CACHÉ CDN</strong> - Usando API de GitHub</p>
    <p>🔄 Actualización: {datetime.now().strftime('%H:%M:%S')}</p>
</div>
""", unsafe_allow_html=True)

