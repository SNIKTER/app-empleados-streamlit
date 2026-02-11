import streamlit as st
import pandas as pd
from github import Github
import base64
import json
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE PÁGINA
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

@st.cache_data(ttl=300)
def obtener_empleados():
    """Lee empleados desde GitHub (datos actualizados cada 5 min)"""
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        contents = repo.get_contents("datos/empleados_actualizado.json")
        df = pd.read_json(base64.b64decode(contents.content).decode('utf-8'))
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

def guardar_solicitud(tipo, datos):
    """Guarda una solicitud en GitHub para ser procesada localmente"""
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
                f"{tipo} - {datos.get('Nombre', datos.get('empleadoId'))}",
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
# MENÚ LATERAL
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
        
        st.dataframe(
            df[['empleadoId', 'Nombre', 'Cargo']],
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
# 2. AGREGAR EMPLEADO
# ============================================
elif menu == "➕ Agregar Empleado":
    st.header("➕ Agregar Nuevo Empleado")
    
    with st.form("form_agregar", clear_on_submit=True):
        nombre = st.text_input("Nombre Completo *")
        cargo = st.text_input("Cargo *")
        
        if st.form_submit_button("💾 Guardar", type="primary"):
            if nombre and cargo:
                with st.spinner("Guardando solicitud..."):
                    datos = {"Nombre": nombre, "Cargo": cargo}
                    success, msg = guardar_solicitud("INSERT", datos)
                    
                    if success:
                        st.success("✅ Solicitud guardada. El empleado se agregará en segundos.")
                        st.info("🔄 Actualiza la lista en 1-2 minutos para ver los cambios.")
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
        empleado_id = st.selectbox(
            "Selecciona empleado",
            df['empleadoId'],
            format_func=lambda x: f"{df[df['empleadoId']==x]['Nombre'].values[0]} - {df[df['empleadoId']==x]['Cargo'].values[0]}"
        )
        
        if empleado_id:
            emp = df[df['empleadoId'] == empleado_id].iloc[0]
            
            with st.form("form_editar"):
                nombre = st.text_input("Nombre", value=emp['Nombre'])
                cargo = st.text_input("Cargo", value=emp['Cargo'])
                
                if st.form_submit_button("🔄 Actualizar", type="primary"):
                    datos = {
                        "empleadoId": int(empleado_id),
                        "Nombre": nombre,
                        "Cargo": cargo
                    }
                    success, msg = guardar_solicitud("UPDATE", datos)
                    
                    if success:
                        st.success("✅ Solicitud de actualización guardada")
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
        empleado_id = st.selectbox(
            "Selecciona empleado",
            df['empleadoId'],
            format_func=lambda x: df[df['empleadoId']==x]['Nombre'].values[0]
        )
        
        if empleado_id:
            nombre = df[df['empleadoId'] == empleado_id]['Nombre'].values[0]
            st.warning(f"⚠️ ¿Eliminar a **{nombre}**?")
            
            if st.button("🗑️ Sí, eliminar", type="primary"):
                datos = {"empleadoId": int(empleado_id)}
                success, msg = guardar_solicitud("DELETE", datos)
                
                if success:
                    st.success("✅ Solicitud de eliminación guardada")
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
    <p>✅ Sistema en tiempo real - Los cambios se procesan en 1-2 minutos</p>
</div>
""", unsafe_allow_html=True)
