import streamlit as st
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Importamos las funciones del archivo de herramientas
from tools_clinica import inicializar_vectorstore

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
    Este sistema utiliza IA (Groq) y búsqueda semántica (FAISS) para responder tus dudas de forma rápida y precisa.
    
    Puedes consultar sobre:
    - 📅 Reserva, cancelación y políticas de turnos.
    - 🏥 Especialidades médicas y horarios de atención.
    - 💳 Obras sociales, prepagas, copagos y preautorizaciones.
    - 📋 Documentación necesaria para tu consulta.
""")


# ============================================================
# 2. INICIALIZACIÓN DEL SISTEMA RAG (CON CACHÉ)
# ============================================================
@st.cache_resource
def cargar_sistema_rag():
    """Carga el vectorstore y configura la cadena RAG una sola vez."""

    ruta_doc1 = os.path.join("data", "doc1_faq.pdf")
    ruta_doc2 = os.path.join("data", "doc2_convenios.pdf")

    if not os.path.exists(ruta_doc1) or not os.path.exists(ruta_doc2):
        st.error(
            f"⚠️ No se encontraron los archivos '{ruta_doc1}' o '{ruta_doc2}'. Por favor, créalos primero."
        )
        return None

    # 1. Inicializar FAISS (esto carga los embeddings y el índice)
    vectorstore = inicializar_vectorstore(ruta_doc1, ruta_doc2)

    # 2. Configurar LLM
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        temperature=0,
        max_tokens=300,
    )

    # 3. Crear el Prompt RAG
    prompt_rag = PromptTemplate(
        template="""Eres un asistente virtual amable, profesional y eficiente de la Clínica de Salud.
Responde la pregunta del paciente usando ÚNICAMENTE la información del contexto proporcionado.

REGLAS:
1. Responde SIEMPRE en español.
2. Sé breve y directo (máximo 3-5 líneas).
3. NO inventes datos. Si la respuesta no está en el contexto, di exactamente: "No tengo esa información específica, te sugiero contactar a recepción al (011) 4567-8900 o por WhatsApp al +54 9 11 1234-5678".

Contexto:
{contexto}

Pregunta del paciente: {pregunta}

Respuesta:""",
        input_variables=["contexto", "pregunta"],
    )

    # 4. Crear la cadena RAG (Recuperación -> Prompt -> LLM -> Parser)
    cadena_rag = prompt_rag | llm | StrOutputParser()

    return {"vectorstore": vectorstore, "cadena_rag": cadena_rag}


# Instanciar el sistema
sistema = cargar_sistema_rag()


# ============================================================
# 3. FUNCIÓN PARA PROCESAR PREGUNTAS
# ============================================================
def responder_pregunta(pregunta: str) -> str:
    """Busca en FAISS y genera una respuesta usando la cadena RAG."""
    if sistema is None:
        return "Error: El sistema no se pudo inicializar. Revisa los archivos PDF."

    # 1. Recuperar los 2 chunks más relevantes de FAISS
    docs = sistema["vectorstore"].similarity_search(pregunta, k=2)
    contexto = "\n\n---\n\n".join([d.page_content for d in docs])

    # 2. Generar la respuesta con el LLM
    respuesta = sistema["cadena_rag"].invoke(
        {"contexto": contexto, "pregunta": pregunta}
    )

    return respuesta


# ============================================================
# 4. INTERFAZ DE USUARIO: ACCIONES RÁPIDAS
# ============================================================
if sistema is not None:
    st.markdown("---")
    st.markdown("### ⚡ Consultas Frecuentes (Acciones Rápidas)")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 ¿Qué documentos debo llevar?", use_container_width=True):
            with st.spinner("Consultando requisitos..."):
                st.session_state["req_convenio"] = responder_pregunta(
                    "¿Qué documentación debo presentar para atenderme por convenio?"
                )

    with col2:
        if st.button("💰 Estimación de copagos", use_container_width=True):
            with st.spinner("Calculando valores referenciales..."):
                st.session_state["copago_ref"] = responder_pregunta(
                    "¿Cuál es el copago referencial para una consulta de medicina general y cardiología?"
                )

    with col3:
        if st.button("📅 Política de turnos", use_container_width=True):
            with st.spinner("Revisando políticas..."):
                st.session_state["pol_turnos"] = responder_pregunta(
                    "¿Cuál es la política de cancelación, no-show y tolerancia de llegada?"
                )

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
    # 5. INTERFAZ DE USUARIO: PREGUNTA LIBRE
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
                    respuesta = responder_pregunta(pregunta_libre)
                    st.success("¡Respuesta encontrada!")
                    st.markdown(respuesta)
                except Exception as e:
                    st.error(f"Ocurrió un error al procesar tu consulta: {str(e)}")

else:
    st.warning(
        "El asistente no pudo iniciarse porque faltan los archivos de documentos. Revisa la consola para más detalles."
    )
