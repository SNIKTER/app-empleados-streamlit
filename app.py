import streamlit as st
import pandas as pd
from github import Github
import base64
import json 
from datetime import datetime

# ============================================
# CONFIGURACIÓN - SOLO LECTURA DE GITHUB
# ============================================
st.set_page_config(
    page_title="Sistema Gestión Empleados",
    page_icon="👔",
    layout="wide"
)

st.title("👔 SISTEMA DE GESTIÓN DE EMPLEADOS")
st.markdown("---")

# ============================================
# CACHÉ DE STREAMLIT (MUY RÁPIDO)
# ============================================
@st.cache_data(ttl=60)  # Cache de 60 segundos
def obtener_empleados():
    """⚡ SOLO LEE DE GITHUB - NUNCA DE SQL SERVER"""
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        
        # Leer datos actualizados (cada 5 min desde SQL Server)
        contents = repo.get_contents("datos/empleados_actualizado.json")
        df = pd.read_json(base64.b64decode(contents.content).decode('utf-8'))
        
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)  # Cache más corto para solicitudes
def obtener_solicitudes_pendientes():
    """Lee solicitudes pendientes (solo para validación)"""
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        
        try:
            contents = repo.get_contents("solicitudes/solicitudes_pendientes.json")
            solicitudes = json.loads(base64.b64decode(contents.content).decode('utf-8'))
            pendientes = [s for s in solicitudes if s.get('estado') == 'pendiente']
            return pendientes
        except:
            return []
    except:
        return []

# ============================================
# FUNCIÓN PARA GUARDAR SOLICITUDES
# ============================================
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
                f"Nueva solicitud {tipo} - {datos.get('empleadoId', '')}",
                json.dumps(solicitudes, indent=2),
                contents.sha
            )
        else:
            repo.create_file(
                "solicitudes/solicitudes_pendientes.json",
                "Inicialización",
                json.dumps(solicitudes, indent=2)
            )
        
        return True, "Solicitud guardada"
    except Exception as e:
        return False, str(e)

# ============================================
# VERIFICAR ID DISPONIBLE
# ============================================
def verificar_id_disponible(df, empleadoId):
    """Verifica si un ID ya existe (usando datos de GitHub)"""
    if df.empty:
        return True
    
    # Verificar en datos actuales
    if empleadoId in df['empleadoId'].values:
        return False
    
    # Verificar en solicitudes pendientes
    pendientes = obtener_solicitudes_pendientes()
    for sol in pendientes:
        if sol['tipo'] == 'INSERT' and sol['datos'].get('empleadoId') == empleadoId:
            return False
    
    return True

# ============================================
# INTERFAZ DE USUARIO
# ============================================
menu = st.sidebar.selectbox(
    "Menú Principal",
    ["📋 Ver Empleados", "➕ Agregar Empleado", "✏️ Editar Empleado", "🗑️ Eliminar Empleado"]
)

# ============================================
# 1. VER EMPLEADOS - ⚡ INSTANTÁNEO (SOLO GITHUB)
# ============================================
if menu == "📋 Ver Empleados":
    st.header("📋 Lista de Empleados")
    
    # ⚡ ESTO ES RAPIDÍSIMO - Lee de GitHub cacheado
    with st.spinner("Cargando..."):
        df = obtener_empleados()
    
    if not df.empty:
        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Empleados", len(df))
        with col2:
            ultima = df['FechaActualizacion'].iloc[0][:10] if 'FechaActualizacion' in df.columns else 'Hoy'
            st.metric("Última actualización", ultima)
        with col3:
            st.metric("IDs disponibles", f"{df['empleadoId'].max() + 1} en adelante")
        
        # Tabla ordenada
        st.dataframe(
            df[['empleadoId', 'Nombre', 'Cargo']].sort_values('empleadoId'),
            use_container_width=True,
            hide_index=True
        )
        
        # Botón descarga
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar Excel",
            csv,
            f"empleados_{datetime.now().strftime('%Y%m%d')}.csv"
        )
    else:
        st.info("No hay empleados registrados")

# ============================================
# 2. AGREGAR EMPLEADO
# ============================================
elif menu == "➕ Agregar Empleado":
    st.header("➕ Agregar Nuevo Empleado")
    
    # Cargar datos actuales para validación
    df = obtener_empleados()
    
    with st.form("form_agregar", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            empleadoId = st.number_input("ID del Empleado *", min_value=1, step=1)
        with col2:
            nombre = st.text_input("Nombre Completo *")
        
        cargo = st.text_input("Cargo *", max_chars=100)
        st.caption(f"Caracteres: {len(cargo)}/100")
        
        if st.form_submit_button("💾 Guardar", type="primary"):
            if empleadoId and nombre and cargo:
                # Validar ID disponible
                if not verificar_id_disponible(df, empleadoId):
                    st.error(f"❌ El ID {empleadoId} ya existe en la base de datos")
                else:
                    with st.spinner("Guardando solicitud..."):
                        datos = {
                            "empleadoId": int(empleadoId),
                            "Nombre": nombre,
                            "Cargo": cargo
                        }
                        success, msg = guardar_solicitud("INSERT", datos)
                        
                        if success:
                            st.success(f"✅ Solicitud guardada - ID: {empleadoId}")
                            st.info("🔄 Los cambios se verán en 1-5 minutos")
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
            "Selecciona ID del empleado",
            sorted(df['empleadoId'].tolist())
        )
        
        if empleadoId:
            emp = df[df['empleadoId'] == empleadoId].iloc[0]
            
            with st.form("form_editar"):
                nombre = st.text_input("Nombre", value=emp['Nombre'])
                cargo = st.text_input("Cargo", value=emp['Cargo'], max_chars=100)
                
                if st.form_submit_button("🔄 Actualizar", type="primary"):
                    datos = {
                        "empleadoId": int(empleadoId),
                        "Nombre": nombre,
                        "Cargo": cargo
                    }
                    success, msg = guardar_solicitud("UPDATE", datos)
                    
                    if success:
                        st.success(f"✅ Solicitud guardada - ID: {empleadoId}")
                    else:
                        st.error(f"❌ Error: {msg}")
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
            "Selecciona ID del empleado",
            sorted(df['empleadoId'].tolist())
        )
        
        if empleadoId:
            nombre = df[df['empleadoId'] == empleadoId]['Nombre'].values[0]
            st.warning(f"⚠️ ¿Eliminar a **{nombre}** (ID: {empleadoId})?")
            
            if st.button("🗑️ Sí, eliminar", type="primary"):
                datos = {"empleadoId": int(empleadoId)}
                success, msg = guardar_solicitud("DELETE", datos)
                
                if success:
                    st.success(f"✅ Solicitud de eliminación guardada - ID: {empleadoId}")
                else:
                    st.error(f"❌ Error: {msg}")
    else:
        st.info("No hay empleados para eliminar")

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>⚡ RÁPIDO: Datos servidos desde caché de GitHub</p>
    <p>🔄 Actualización automática cada 60 segundos</p>
</div>
""", unsafe_allow_html=True)

