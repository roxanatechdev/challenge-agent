import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor

# Importamos las funciones del archivo de herramientas que creamos antes
# Asegúrate de que este archivo se llame 'tools_clinica.py' y esté en la misma carpeta
from tools_clinica import inicializar_vectorstore, crear_herramientas_clinica

# Cargar variables de entorno
load_dotenv()

# ============================================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Asistente Virtual - Clínica de Salud", page_icon="🏥", layout="centered"
)

st.title("🏥 Asistente Virtual de la Clínica de Salud")

st.info(""" 
    **Bienvenido al asistente inteligente de la clínica.** 
    Este agente utiliza IA (LangChain + Groq) y búsqueda semántica (FAISS) para responder tus dudas de forma rápida y precisa.
    
    Puedes consultar sobre:
    - 📅 Reserva, cancelación y políticas de turnos.
    - 🏥 Especialidades médicas y horarios de atención.
    - 💳 Obras sociales, prepagas, copagos y preautorizaciones.
    - 📋 Documentación necesaria para tu consulta.
    """)


# ============================================================
# 2. INICIALIZACIÓN DEL AGENTE (CON CACHÉ PARA RENDIMIENTO)
# ============================================================
@st.cache_resource
def cargar_agente_clinica():
    """Carga el vectorstore y el agente una sola vez para optimizar recursos."""

    # Rutas de los documentos
    ruta_doc1 = "doc1_faq.pdf"
    ruta_doc2 = "doc2_convenios.pdf"

    # Verificar que los archivos existan antes de cargar
    if not os.path.exists(ruta_doc1) or not os.path.exists(ruta_doc2):
        st.error(
            f"⚠️ No se encontraron los archivos '{ruta_doc1}' o '{ruta_doc2}'. Por favor, créalos primero."
        )
        return None

    # 1. Inicializar FAISS
    inicializar_vectorstore(ruta_doc1, ruta_doc2)

    # 2. Configurar LLM (Temperature 0 para precisión, max_tokens bajo para ahorrar)
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=300,
    )

    # 3. Obtener herramientas
    tools = crear_herramientas_clinica()

    # 4. Prompt ReAct optimizado para la clínica
    prompt_react_clinica = PromptTemplate(
        template="""Eres un asistente virtual amable, profesional y eficiente de la Clínica de Salud. Tu objetivo es ayudar a los pacientes con sus dudas.

    Tienes acceso a las siguientes herramientas:
    {tools}

    Los nombres de las herramientas son: {tool_names}

    REGLAS OBLIGATORIAS:
    1. Responde SIEMPRE en español.
    2. Sé breve y directo (máximo 3-5 líneas). No des explicaciones innecesarias.
    3. Usa las herramientas proporcionadas para obtener la información. NO inventes datos.
    4. Si la herramienta no tiene la información, indica amablemente: "No tengo esa información específica, te sugiero contactar a recepción al (011) 4567-8900 o por WhatsApp al +54 9 11 1234-5678".
    5. Usa el formato de pensamiento (Thought/Action/Observation) internamente, pero tu Respuesta Final debe ser solo el mensaje para el paciente, sin mostrar el proceso interno.

    Comienza.

    Pregunta: {input}
    Pensamiento: {agent_scratchpad}""",
        input_variables=["input", "agent_scratchpad"],
        partial_variables={"tools": "", "tool_names": ""},
    )

    # 5. Crear Agente y Ejecutor
    agente = create_react_agent(llm=llm, tools=tools, prompt=prompt_react_clinica)
    orquestador = AgentExecutor(
        agent=agente,
        tools=tools,
        verbose=False,  # Cambiar a True solo para depuración
        handle_parsing_errors=True,
    )

    return orquestador


# Instanciar el agente
orquestador = cargar_agente_clinica()

# ============================================================
# 3. INTERFAZ DE USUARIO: ACCIONES RÁPIDAS
# ============================================================
if orquestador is not None:
    st.markdown("---")
    st.markdown("### ⚡ Consultas Frecuentes (Acciones Rápidas)")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 ¿Qué documentos debo llevar?", use_container_width=True):
            with st.spinner("Consultando requisitos..."):
                respuesta = orquestador.invoke(
                    {
                        "input": "¿Qué documentación debo presentar para atenderme por convenio?"
                    }
                )
                st.session_state["req_convenio"] = respuesta["output"]

    with col2:
        if st.button("💰 Estimación de copagos", use_container_width=True):
            with st.spinner("Calculando valores referenciales..."):
                respuesta = orquestador.invoke(
                    {
                        "input": "¿Cuál es el copago referencial para una consulta de medicina general y cardiología?"
                    }
                )
                st.session_state["copago_ref"] = respuesta["output"]

    with col3:
        if st.button("📅 Política de turnos", use_container_width=True):
            with st.spinner("Revisando políticas..."):
                respuesta = orquestador.invoke(
                    {
                        "input": "¿Cuál es la política de cancelación, no-show y tolerancia de llegada?"
                    }
                )
                st.session_state["pol_turnos"] = respuesta["output"]

    # Mostrar resultados de acciones rápidas en expanders
    if "req_convenio" in st.session_state:
        with st.expander("📋 Requisitos de Atención", expanded=True):
            st.markdown(st.session_state["req_convenio"])

    if "copago_ref" in st.session_state:
        with st.expander("💰 Estimación de Copagos", expanded=True):
            st.markdown(st.session_state["copago_ref"])

    if "pol_turnos" in st.session_state:
        with st.expander("📅 Política de Turnos", expanded=True):
            st.markdown(st.session_state["pol_turnos"])

    # ============================================================
    # 4. INTERFAZ DE USUARIO: PREGUNTA LIBRE
    # ============================================================
    st.markdown("---")
    st.markdown("### 💬 Haz tu propia pregunta")
    st.caption(
        "Ejemplos: '¿Atienden por OSDE?', '¿Tienen servicio de guardia los fines de semana?', '¿Cómo pido un reintegro?'"
    )

    pregunta_libre = st.text_input(
        "Escribe tu consulta aquí:",
        placeholder="Ej: ¿Con cuánta anticipación debo pedir turno para cardiología?",
        label_visibility="collapsed",
    )

    if st.button("Enviar consulta", type="primary"):
        if pregunta_libre.strip() == "":
            st.warning("Por favor, escribe una pregunta.")
        else:
            with st.spinner("El asistente está buscando la mejor respuesta..."):
                try:
                    respuesta = orquestador.invoke({"input": pregunta_libre})
                    st.success("¡Respuesta encontrada!")
                    st.markdown(respuesta["output"])
                except Exception as e:
                    st.error(f"Ocurrió un error al procesar tu consulta: {str(e)}")

else:
    st.warning(
        "El asistente no pudo iniciarse porque faltan los archivos de documentos. Revisa la consola para más detalles."
    )
