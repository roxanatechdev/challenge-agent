# 🏥 Asistente Virtual Inteligente - Clínica de Salud

## 📋 Descripción General

Este proyecto implementa un **asistente virtual inteligente** para una clínica de salud, diseñado para responder de forma automática, precisa y amable las consultas más frecuentes de los pacientes.

El agente utiliza **Inteligencia Artificial Generativa** combinada con **Recuperación Aumentada por Generación (RAG)** para acceder a información institucional actualizada (FAQs, convenios, políticas) y generar respuestas contextuales, evitando alucinaciones y derivando a canales humanos cuando la información no está disponible.

### 🎯 Objetivos del proyecto

- 🚀 Automatizar respuestas a consultas frecuentes de pacientes (turnos, requisitos, coberturas).
- 💰 Reducir la carga operativa del personal de recepción.
- ⚡ Ofrecer respuestas rápidas (3-5 líneas) optimizadas en consumo de tokens.
- 🔒 Minimizar alucinaciones mediante RAG con FAISS y prompts estrictos.
- 📱 Proveer una interfaz web amigable con Streamlit.

## 🖥️ Vista Previa de la Interfaz
<img src="assets/01_interfaz_principal.png" width="350" alt="Interfaz">
---

## 🏗️ Arquitectura de la Solución

### Diagrama de flujo

<img src="assets/diagrama_arquitectura.png" width="300" alt="Diagrama de Arquitectura">
  
### Componentes principales

1. **Frontend (Streamlit)**: Interfaz web con acciones rápidas y chat libre.
2. **Agente React (LangChain)**: Orquesta el razonamiento y decide qué herramienta usar.
3. **LLM (Groq + Llama 3.1 8B)**: Modelo rápido y eficiente para generar respuestas.
4. **Vectorstore (FAISS)**: Almacena embeddings de los documentos para búsqueda semántica.
5. **Herramientas especializadas**:
   - `consultar_base_conocimiento`: RAG sobre los documentos institucionales.
   - `verificar_requisitos_atencion`: Checklist según modalidad (convenio/particular).
   - `calcular_copago_referencial`: Estimación de valores según especialidad.

---

## 🛠️ Tecnologías y Herramientas Utilizadas

| Tecnología | Versión | Propósito |
|---|---|---|
| **Python** | 3.11+ | Lenguaje base del proyecto |
| **LangChain** | 0.3.22 | Framework para orquestar agentes y RAG |
| **LangChain-Groq** | 0.3.2 | Integración con el LLM de Groq |
| **Groq API** | - | Infraestructura rápida para Llama 3.1 8B |
| **Llama 3.1 8B Instant** | - | Modelo de lenguaje generativo |
| **FAISS** | - | Búsqueda vectorial de similitud |
| **Sentence-Transformers** | - | Generación de embeddings multilingües |
| **PyPDF** | 5.4.0 | Extracción de texto de documentos PDF |
| **Streamlit** | 1.44.1 | Framework de interfaz web |
| **Python-dotenv** | 1.0.1 | Gestión de variables de entorno |

---

## 🚀 Instrucciones para Ejecutar el Proyecto

### 1. Clonar o crear el proyecto

```bash
mkdir consultorio-ia
cd consultorio-ia
```

2. Crear un entorno virtual
   
```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
source .venv/bin/activate # Linux/Mac
```

3. Instalar dependencias
Crea un archivo requirements.txt E instala:

```bash
pip install -r requirements.txt
```
4. Configurar variables de entorno
Crea un archivo .env en la raíz del proyecto:

```env
GROQ_API_KEY=tu_clave_groq_aqui
```

7. Ejecutar la aplicación
```bash
streamlit run app.py
```
La aplicación se abrirá automáticamente en tu navegador en http://localhost:8501.

## 💬 Ejemplos de Preguntas que el Agente Puede Responder

### 📅 Turnos y Agenda

- "¿Con cuánta anticipación debo pedir turno para cardiología?"
- "¿Qué pasa si llego tarde a mi turno?"
- "¿Puedo cancelar mi turno el mismo día?"
- "¿Atienden urgencias sin turno previo?"

### 💳 Coberturas y Pagos

- "¿Qué obras sociales aceptan?"
- "¿Atienden por OSDE?"
- "¿Cuánto cuesta la consulta con un especialista?"
- "¿Cómo puedo pedir un reintegro?"

### 📋 Requisitos

- "¿Qué documentos debo llevar a mi consulta?"
- "¿Necesito orden médica para dermatología?"
- "¿Qué pasa si no tengo obra social?"

### 🏥 Información General

- "¿Cuáles son los horarios de atención?"
- "¿Dónde está ubicada la clínica?"
- "¿Tienen servicio de WhatsApp?"

---

## 💬 Ejemplos de Uso y Respuestas del Agente

### 📸 Demostración Visual

A continuación, ejemplos reales de interacciones con el asistente:

#### 1️⃣ Interfaz y Acciones Rápidas

<img src="assets/interfaz-app-respuestas-rapidas.png" width="450" style="border: 1px solid #d0d7de; border-radius: 8px; padding: 10px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"/>

#### 2️⃣ Consulta sobre Requisitos de Atención

**Pregunta:** "¿Qué documentos debo llevar si me atiende por convenio?"

<img src="assets/02_requisitos_convenio.png" width="450" style="border: 1px solid #d0d7de; border-radius: 8px; padding: 10px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"/>

#### 3️⃣ Consulta sobre Copagos

**Pregunta:** "¿Cuánto cuesta la consulta con un especialista?"

<img src="assets/03_copago_especialista.png" width="450" style="border: 1px solid #d0d7de; border-radius: 8px; padding: 10px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"/>

#### 4️⃣ Consulta sobre Política de Turnos

**Pregunta:** "¿Con cuánta anticipación debo pedir turno para cardiología?"

<img src="assets/04_turnos_cardiologia.png" width="450" style="border: 1px solid #d0d7de; border-radius: 8px; padding: 10px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"/>

#### 5️ Pregunta Libre (Chat)

**Pregunta:** "¿Atienden por Swiss Medical?"

<img src="assets/05_swiss_medical.png" width="450" style="border: 1px solid #d0d7de; border-radius: 8px; padding: 10px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"/>

---

## 📊 Optimizaciones Implementadas

|Aspecto|Implementación|Beneficio|
|---|---|---|
|**Tokens limitados**|`max_tokens=300` en el LLM|Respuestas cortas, menor costo en Groq|
|**Embeddings locales**|`sentence-transformers` multilingüe|Sin dependencia de APIs externas|
|**Chunking inteligente**|Separador por pregunta (`\n\n¿`)|Cada chunk = 1 pregunta + 1 respuesta|
|**Caché en Streamlit**|`@st.cache_resource`|Vectorstore se carga una sola vez|
|**Retrieval limitado**|`k=2` en FAISS|Solo se envían 2 chunks al LLM|

---

## 📝 Licencia

Este proyecto fue desarrollado con fines educativos y de demostración.