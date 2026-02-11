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

# ============================================
# FUNCIONES DE GITHUB (ESCRITURA)
# ============================================

def guardar_solicitud_en_github(tipo, datos):
    """
    Guarda una solicitud de INSERT/UPDATE/DELETE en GitHub
    """
    try:
        # Conectar a GitHub
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        
        # Leer solicitudes pendientes
        try:
            contents = repo.get_contents("solicitudes/solicitudes_pendientes.json")
            solicitudes = json.loads(base64.b64decode(contents.content).decode('utf-8'))
        except:
            solicitudes = []
        
        # Agregar nueva solicitud
        nueva_solicitud = {
            "id": len(solicitudes) + 1,
            "tipo": tipo,
            "datos": datos,
            "fecha_solicitud": datetime.now().isoformat(),
            "estado": "pendiente"
        }
        solicitudes.append(nueva_solicitud)
        
        # Guardar en GitHub
        try:
            repo.update_file(
                "solicitudes/solicitudes_pendientes.json",
                f"Nueva solicitud {tipo} - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                json.dumps(solicitudes, indent=2),
                contents.sha
            )
        except:
            repo.create_file(
                "solicitudes/solicitudes_pendientes.json",
                f"Creación archivo solicitudes",
                json.dumps(solicitudes, indent=2)
            )
        
        return True, "Solicitud guardada correctamente"
    except Exception as e:
        return False, str(e)

def obtener_empleados():
    """Lee empleados desde GitHub (datos actualizados)"""
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(st.secrets["GITHUB_REPO"])
        contents = repo.get_contents("datos/empleados_actualizado.json")
        df = pd.read_json(base64.b64decode(contents.content).decode('utf-8'))
        return df
    except:
        return pd.DataFrame()

# ============================================
# INTERFAZ DE USUARIO
# ============================================
st.title("👔 SISTEMA DE GESTIÓN DE EMPLEADOS")
st.markdown("---")

# MENÚ
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
        st.metric("Total Empleados", len(df))
        st.dataframe(df[['empleadoId', 'Nombre', 'Cargo']], use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Excel", data=csv, file_name=f"empleados_{datetime.now().strftime('%Y%m%d')}.csv")
    else:
        st.info("No hay empleados registrados")

# ============================================
# 2. AGREGAR EMPLEADO (GUARDA EN GITHUB)
# ============================================
elif menu == "➕ Agregar Empleado":
    st.header("➕ Agregar Nuevo Empleado")
    
    with st.form("form_agregar", clear_on_submit=True):
        nombre = st.text_input("Nombre Completo *")
        cargo = st.text_input("Cargo *")
        
        if st.form_submit_button("💾 Guardar", type="primary"):
            if nombre and cargo:
                with st.spinner("Guardando solicitud en GitHub..."):
                    datos = {
                        "Nombre": nombre,
                        "Cargo": cargo,
                        "fecha": datetime.now().isoformat()
                    }
                    success, message = guardar_solicitud_en_github("INSERT", datos)
                    
                    if success:
                        st.success("✅ Solicitud guardada. Se procesará en segundos.")
                        st.info("🔄 El sistema actualizará automáticamente en 1-2 minutos.")
                        st.balloons()
                    else:
                        st.error(f"❌ Error: {message}")
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
            options=df['empleadoId'],
            format_func=lambda x: f"{df[df['empleadoId']==x]['Nombre'].values[0]}"
        )
        
        if empleado_id:
            empleado = df[df['empleadoId'] == empleado_id].iloc[0]
            
            with st.form("form_editar"):
                nuevo_nombre = st.text_input("Nombre", value=empleado['Nombre'])
                nuevo_cargo = st.text_input("Cargo", value=empleado['Cargo'])
                
                if st.form_submit_button("🔄 Actualizar", type="primary"):
                    datos = {
                        "empleadoId": int(empleado_id),
                        "Nombre": nuevo_nombre,
                        "Cargo": nuevo_cargo
                    }
                    success, message = guardar_solicitud_en_github("UPDATE", datos)
                    
                    if success:
                        st.success("✅ Solicitud de actualización guardada")
                        st.info("🔄 Se procesará en segundos")
                    else:
                        st.error(f"❌ Error: {message}")
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
            options=df['empleadoId'],
            format_func=lambda x: f"{df[df['empleadoId']==x]['Nombre'].values[0]}"
        )
        
        if empleado_id:
            nombre = df[df['empleadoId'] == empleado_id]['Nombre'].values[0]
            st.warning(f"⚠️ ¿Eliminar a **{nombre}**?")
            
            if st.button("🗑️ Sí, eliminar", type="primary"):
                datos = {"empleadoId": int(empleado_id)}
                success, message = guardar_solicitud_en_github("DELETE", datos)
                
                if success:
                    st.success("✅ Solicitud de eliminación guardada")
                    st.info("🔄 Se procesará en segundos")
                else:
                    st.error(f"❌ Error: {message}")
    else:
        st.info("No hay empleados para eliminar")
