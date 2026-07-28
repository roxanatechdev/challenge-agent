import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings

# ============================================================
# 1. CONFIGURACIÓN INICIAL
# ============================================================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# LLM optimizado para respuestas cortas (temperature bajo = menos alucinaciones)
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=300,  # Limita la respuesta para ahorrar tokens
)


# Embeddings usando la API gratuita de HuggingFace (no requiere PyTorch local)

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2",  # Modelo más ligero, funciona sin torchvision
    model_kwargs={"device": "cpu"},
)

# ============================================================
# 2. CARGA Y VECTORIZACIÓN DE DOCUMENTOS (FAISS)
# ============================================================
from langchain_community.document_loaders import PyPDFLoader


def cargar_documentos_clinica(ruta_doc1: str, ruta_doc2: str) -> FAISS:
    """
    Carga los dos documentos PDF de la clínica, los divide en chunks autocontenidos
    (una pregunta-respuesta por chunk) y construye el índice FAISS.
    """
    documentos = []

    for ruta in [ruta_doc1, ruta_doc2]:
        # PyPDFLoader extrae el texto del PDF y devuelve objetos Document
        loader = PyPDFLoader(ruta)
        docs_pdf = loader.load()

        # Dividir cada página en chunks más pequeños (una pregunta-respuesta por chunk)
        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n¿", "\n\nSección", "\n\n", "\n"],
            chunk_size=800,
            chunk_overlap=50,
            length_function=len,
        )

        chunks = splitter.split_documents(docs_pdf)
        documentos.extend(chunks)

    # Construcción del índice FAISS
    vectorstore = FAISS.from_documents(documentos, embeddings)
    return vectorstore


# Variable global para el vectorstore (se inicializa al arrancar la app)
vectorstore_clinica = None


def inicializar_vectorstore(ruta_doc1: str, ruta_doc2: str):
    """Inicializa el vectorstore una sola vez al iniciar la aplicación."""
    global vectorstore_clinica
    vectorstore_clinica = cargar_documentos_clinica(ruta_doc1, ruta_doc2)
    return vectorstore_clinica


# ============================================================
# 3. HERRAMIENTA 1: CONSULTA A LA BASE DE CONOCIMIENTO (RAG)
# ============================================================
@tool
def consultar_base_conocimiento(pregunta: str) -> str:
    """
    Utiliza esta herramienta SIEMPRE que el usuario haga preguntas sobre:
    - Reserva, cancelación o reagendamiento de turnos
    - Especialidades médicas disponibles
    - Horarios, ubicación o canales de contacto
    - Obras sociales, coberturas, copagos o preautorizaciones
    - Requisitos de documentación para la atención
    - Política de puntualidad o no-show
    - Reintegros y modalidad particular
    - Preparación para consultas o estudios

    NO uses esta herramienta para saludos, despedidas o preguntas fuera del
    contexto de la clínica.
    """
    if vectorstore_clinica is None:
        return "⚠️ La base de conocimiento aún no ha sido inicializada."

    # Recuperación de máximo 2 chunks (ahorra tokens)
    docs = vectorstore_clinica.similarity_search(pregunta, k=2)
    contexto = "\n\n---\n\n".join([d.page_content for d in docs])

    template = PromptTemplate(
        template="""Eres el asistente virtual de la Clínica de Salud. Responde la pregunta del paciente usando ÚNICAMENTE la información del contexto proporcionado.

REGLAS:
1. Responde en máximo 3 a 5 líneas, de forma clara y amable.
2. Si la respuesta no está en el contexto, di: "No tengo esa información, te sugiero contactar a recepción al (011) 4567-8900."
3. No inventes datos ni agregues información externa.
4. Usa un tono profesional pero cercano.

Contexto:
{contexto}

Pregunta del paciente: {pregunta}

Respuesta:""",
        input_variables=["contexto", "pregunta"],
    )

    cadena = template | llm | StrOutputParser()
    return cadena.invoke({"contexto": contexto, "pregunta": pregunta})


# ============================================================
# 4. HERRAMIENTA 2: VERIFICAR REQUISITOS DE ATENCIÓN
# ============================================================
@tool
def verificar_requisitos_atencion(tipo_atencion: str) -> str:
    """
    Utiliza esta herramienta cuando el paciente pregunte qué debe llevar,
    qué documentación necesita, o qué requisitos debe cumplir antes de su consulta.

    Parámetros:
    - tipo_atencion: puede ser "convenio" (con obra social/prepaga) o "particular"

    Devuelve un checklist claro de lo que el paciente debe presentar.
    """
    tipo = tipo_atencion.strip().lower()

    if "convenio" in tipo or "obra social" in tipo or "prepaga" in tipo:
        respuesta = (
            "📋 *Requisitos para atención por convenio:*\n"
            "1. DNI o pasaporte vigente.\n"
            "2. Credencial digital o física de tu obra social / medicina prepaga (con el plan visible).\n"
            "3. Orden médica autorizada (solo si la especialidad o estudio lo requiere previamente).\n\n"
            "Sin estos documentos no podremos brindarte la atención bajo cobertura."
        )
    elif "particular" in tipo:
        respuesta = (
            "📋 *Requisitos para atención particular:*\n"
            "1. DNI o pasaporte vigente.\n"
            "2. Medio de pago (efectivo, tarjeta de débito o crédito).\n"
            "3. Se te entregará factura oficial para que gestiones el reintegro ante tu obra social si tu plan lo contempla.\n\n"
            "Si tu seguro no tiene convenio con la clínica, esta es la modalidad adecuada."
        )
    else:
        respuesta = (
            "📋 *Requisitos generales para la atención:*\n"
            "- DNI o pasaporte vigente.\n"
            "- Si tienes obra social / prepaga con convenio: credencial vigente.\n"
            "- Orden médica autorizada si la especialidad o estudio lo requiere.\n\n"
            "¿Tu atención será por convenio o particular? Así te detallo los requisitos específicos."
        )

    return respuesta


# ============================================================
# 5. HERRAMIENTA 3: CALCULAR COPAGO REFERENCIAL
# ============================================================
@tool
def calcular_copago_referencial(especialidad: str) -> str:
    """
    Utiliza esta herramienta cuando el paciente pregunte cuánto cuesta la consulta,
    cuál es el copago, o el valor de la atención por una especialidad específica.

    Parámetros:
    - especialidad: nombre de la especialidad (ej. 'medicina general', 'cardiología', 'pediatría')

    Devuelve un valor referencial en pesos argentinos (ARS).
    """
    esp = especialidad.strip().lower()

    # Tabla de referencia según Documento 2
    if any(x in esp for x in ["general", "pediatría", "pediatria"]):
        minimo, maximo = 2000, 4000
        tipo = "consulta de Medicina General / Pediatría"
    elif any(
        x in esp
        for x in [
            "cardiología",
            "neurología",
            "ginecología",
            "traumatología",
            "dermatología",
            "psicología",
            "especialista",
        ]
    ):
        minimo, maximo = 4000, 8000
        tipo = "consulta de especialidad"
    elif any(x in esp for x in ["imagen", "estudio", "ecografía", "rmn", "tac"]):
        return (
            f"🔎 Para estudios de diagnóstico por imagen, el valor varía según el estudio específico. "
            f"Te recomiendo consultar el valor exacto llamando a recepción al (011) 4567-8900 "
            f"o por WhatsApp al +54 9 11 1234-5678 indicando qué estudio necesitas."
        )
    else:
        minimo, maximo = 4000, 8000
        tipo = "consulta"

    return (
        f"💰 *Copago referencial para {type}:*\n"
        f"El valor estimado es entre ${minimo:,} y ${maximo:,} ARS, dependiendo del plan de tu obra social o medicina prepaga.\n\n"
        f"⚠️ Este valor es orientativo. El copago exacto se confirma al momento de la admisión según tu plan específico."
    ).replace("{type}", tipo)


# ============================================================
# 6. FUNCIÓN PARA CREAR EL LISTADO DE HERRAMIENTAS
# ============================================================
def crear_herramientas_clinica():
    """
    Retorna la lista de herramientas disponibles para el agente de la clínica.
    Cada herramienta está optimizada para consumir pocos tokens en Groq.
    """
    return [
        consultar_base_conocimiento,
        verificar_requisitos_atencion,
        calcular_copago_referencial,
    ]


# ============================================================
# 7. BLOQUE DE PRUEBA
# ============================================================
if __name__ == "__main__":
    # Inicializar vectorstore con los documentos
    vs = inicializar_vectorstore("doc1_faq.txt", "doc2_convenios.txt")
    print(f"✅ Vectorstore inicializado con {vs.index.ntotal} chunks.")

    # Probar cada herramienta
    herramientas = crear_herramientas_clinica()

    print("\n--- Prueba 1: consultar_base_conocimiento ---")
    print(herramientas[0].invoke("¿Cuánto tiempo antes debo llegar a mi turno?"))

    print("\n--- Prueba 2: verificar_requisitos_atencion ---")
    print(herramientas[1].invoke("convenio"))

    print("\n--- Prueba 3: calcular_copago_referencial ---")
    print(herramientas[2].invoke("cardiología"))
