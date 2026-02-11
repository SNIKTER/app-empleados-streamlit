import streamlit as st
import pandas as pd
from github import Github
import base64
import json
from datetime import datetime

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
# FUNCIONES GITHUB
# ============================================
@st.cache_data(ttl=300)
def obtener_empleados():
    """Lee empleados desde GitHub"""
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        contents = repo.get_contents("datos/empleados_actualizado.json")
        df = pd.read_json(base64.b64decode(contents.content).decode('utf-8'))
        return df
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
                f"{tipo} - {datos.get('empleadoId', datos.get('Nombre'))}",
                json.dumps(solicitudes, indent=2),
                contents.sha
            )
        else:
            repo.create_file(
                "solicitudes/solicitudes_pendientes.json",
                "Inicialización",
                json.dumps(solicitudes, indent=2)
            )
        
        return True, "Solicitud guardada correctamente"
    except Exception as e:
        return False, str(e)

# ============================================
# VERIFICAR ID DUPLICADO
# ============================================
def verificar_id_disponible(df, empleadoId):
    """Verifica si un ID ya existe en la tabla"""
    if df.empty:
        return True
    return empleadoId not in df['empleadoId'].values

# ============================================
# MENÚ
# ============================================
menu = st.sidebar.selectbox(
    "Menú Principal",
    ["📋 Ver Empleados", "➕ Agregar Empleado", "✏️ Editar Empleado", "🗑️ Eliminar Empleado"]
)

# ============================================
# 1. VER EMPLEADOS
# ============================================
if menu == "📋 Ver Empleados":
    st.header("📋 Lista de Empleados")
    
    df = obtener_empleados()
    
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Empleados", len(df))
        with col2:
            st.metric("Último ID", df['empleadoId'].max())
        
        st.dataframe(
            df[['empleadoId', 'Nombre', 'Cargo']].sort_values('empleadoId'),
            use_container_width=True,
            hide_index=True
        )
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar Excel",
            csv,
            f"empleados_{datetime.now().strftime('%Y%m%d')}.csv"
        )
    else:
        st.info("No hay empleados registrados")

# ============================================
# 2. AGREGAR EMPLEADO (CON VALIDACIÓN DE ID)
# ============================================
elif menu == "➕ Agregar Empleado":
    st.header("➕ Agregar Nuevo Empleado")
    
    df = obtener_empleados()
    
    with st.form("form_agregar", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            empleadoId = st.number_input("ID del Empleado *", min_value=1, step=1)
        with col2:
            nombre = st.text_input("Nombre Completo *")
        
        cargo = st.text_input("Cargo *")
        
        if st.form_submit_button("💾 Guardar", type="primary"):
            if empleadoId and nombre and cargo:
                # VALIDAR ID DUPLICADO
                if not verificar_id_disponible(df, empleadoId):
                    st.error(f"❌ El ID {empleadoId} ya existe en la base de datos")
                    st.info("💡 Por favor, usa un ID diferente")
                else:
                    with st.spinner("Guardando solicitud..."):
                        datos = {
                            "empleadoId": int(empleadoId),
                            "Nombre": nombre,
                            "Cargo": cargo
                        }
                        success, msg = guardar_solicitud("INSERT", datos)
                        
                        if success:
                            st.success(f"✅ Solicitud guardada. Empleado ID: {empleadoId}")
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
                cargo = st.text_input("Cargo", value=emp['Cargo'])
                
                if st.form_submit_button("🔄 Actualizar", type="primary"):
                    datos = {
                        "empleadoId": int(empleadoId),
                        "Nombre": nombre,
                        "Cargo": cargo
                    }
                    success, msg = guardar_solicitud("UPDATE", datos)
                    
                    if success:
                        st.success(f"✅ Solicitud de actualización guardada - ID: {empleadoId}")
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
    <p>✅ IDs MANUALES - Validación de duplicados</p>
</div>
""", unsafe_allow_html=True)
