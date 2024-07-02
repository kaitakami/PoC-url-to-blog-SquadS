import streamlit as st
from openai import OpenAI
import requests
import os

# Page title
st.set_page_config(page_title='SquadS Blog from URLs generator', page_icon='📝')
st.title('📝 SquadS Blog from URLs generator')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize session state
if 'ideas' not in st.session_state:
    st.session_state.ideas = []
if 'generated_blogs' not in st.session_state:
    st.session_state.generated_blogs = {}
if 'urls' not in st.session_state:
    st.session_state.urls = [""]

# Function to add a new URL input field
def add_url():
    st.session_state.urls.append("")

# Function to remove a URL input field
def remove_url(index):
    st.session_state.urls.pop(index)
    if not st.session_state.urls:
        st.session_state.urls = [""]

# Function to retrieve website content
def get_website_content(url):
    api_url = f"https://r.jina.ai/{url}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.text
    else:
        return f"Error al obtener contenido del sitio web: {response.status_code}"

# Function to generate blog ideas
def generate_blog_ideas(website_contents, num_ideas, tone, length, model):
    prompt = f"""
    Basándote en el siguiente contenido de sitios web, genera {num_ideas} ideas para blogs.
    Usa un tono {tone} y apunta a aproximadamente {length} caracteres por idea de blog.
    
    Contenido de los sitios web:
    {website_contents}
    
    Por favor, devuelve las ideas en el siguiente formato:
    1. [Título de la idea]: Breve descripción de la idea.
    2. [Título de la idea]: Breve descripción de la idea.
    3. [Título de la idea]: Breve descripción de la idea.
    ...

    Ejemplo:
    1. El Poder de la Colaboración en el Emprendimiento: El Enfoque de SquadS Ventures: Conoce en detalle cómo SquadS Ventures fomenta la colaboración como un motor fundamental para el crecimiento sostenible de los negocios. Exploraremos cómo las alianzas estratégicas pueden potenciar el impacto positivo de las startups en la región, generando sinergias que fortalecen la resiliencia y adaptabilidad de las empresas emergentes.

    La idea y la descripción deben que estar en la misma linea. 
    
    Asegúrate de que cada idea sea única, interesante y relevante para el contenido proporcionado.
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Eres un asistente útil que genera ideas creativas y relevantes para blogs basadas en el contenido de sitios web."},
            {"role": "user", "content": prompt}
        ]
    )
    
    ideas = response.choices[0].message.content.split("\n")
    return [idea.strip() for idea in ideas if idea.strip()]

# Function to generate blog content
def generate_blog_content(idea, website_contents, tone, length, model):
    prompt = f"""
    Escribe una entrada de blog basada en la siguiente idea: '{idea}'.
    Usa un tono {tone} y apunta a aproximadamente {length} caracteres.
    
    Utiliza el siguiente contenido de sitios web como inspiración y fuente de información:
    {website_contents}

    Solo retorna el blog, es innecesario compartir información que no aporta al usuario. Este blog será directamente publicado al blog oficial por lo que por favor evita retornar información innecesaria al lector.
    
    Retorna el blog en Markdown, incluyendo encabezados apropiados, párrafos y cualquier formato relevante.
    Asegúrate de que el contenido sea original, bien estructurado y atractivo para los lectores.
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Eres un asistente útil que escribe entradas de blog en formato Markdown, utilizando contenido de sitios web como inspiración."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

# Function to display ideas as cards and handle blog generation
def display_idea_cards():
    for i, idea in enumerate(st.session_state.ideas):
        with st.expander(f"{idea[:100]}...", expanded=True):
            st.write(idea)
            if f"blog_{i}" not in st.session_state.generated_blogs:
                if st.button(f"Generar Blog para la Idea {i+1}", key=f"gen_blog_{i}"):
                    with st.spinner("Generando blog..."):
                        website_contents = "\n".join([get_website_content(url) for url in st.session_state.urls if url.strip()])
                        content = generate_blog_content(idea, website_contents, st.session_state.tone, st.session_state.length, st.session_state.model)
                        st.session_state.generated_blogs[f"blog_{i}"] = content
                    st.success("¡Blog generado con éxito!")
                    # st.rerun()
            
            if f"blog_{i}" in st.session_state.generated_blogs:
                st.markdown(st.session_state.generated_blogs[f"blog_{i}"])
                
                # Refinement interface
                user_input = st.text_input("Haz una pregunta o sugiere una mejora:", key=f"refine_input_{i}")
                if st.button("Refinar Blog", key=f"refine_button_{i}"):
                    refined_content = refine_blog(st.session_state.generated_blogs[f"blog_{i}"], user_input, st.session_state.model)
                    st.session_state.generated_blogs[f"blog_{i}"] = refined_content
                    # st.rerun()

# Function to refine blog
def refine_blog(original_content, user_input, model):
    prompt = f"""
    Contenido original del blog (en formato Markdown):

    {original_content}

    Solicitud del usuario: {user_input}

    Por favor, refina la entrada del blog basándote en la solicitud del usuario. Asegúrate de que el blog refinado siga en formato Markdown y mantenga un tono y estilo coherentes con el original.
    """
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Eres un asistente útil que refina entradas de blog manteniendo el formato Markdown y mejorando el contenido según las solicitudes de los usuarios."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

# Sidebar for accepting input parameters
with st.sidebar:
    st.header('1. Parámetros de Entrada')
    
    # Improved URL input
    st.subheader("Ingrese URLs")
    for i, url in enumerate(st.session_state.urls):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.session_state.urls[i] = st.text_input(f"URL {i+1}", value=url, key=f"url_{i}")
        with col2:
            if st.button("Eliminar", key=f"remove_{i}"):
                remove_url(i)
    
    if st.button("Agregar URL"):
        add_url()

    num_ideas = st.slider('Número de ideas para blogs', 1, 15, 5)
    st.session_state.tone = st.text_input('Tono para la generación del blog', 'profesional')
    st.session_state.length = st.slider('Longitud aproximada del blog (caracteres)', 250, 10000, 1000)
    st.session_state.model = st.selectbox('Seleccione el modelo de OpenAI', ['gpt-3.5-turbo', 'gpt-4o'])
    
    if st.button('Generar Ideas'):
        with st.spinner('Generando ideas para blogs...'):
            valid_urls = [url for url in st.session_state.urls if url.strip()]
            if valid_urls:
                website_contents = "\n".join([get_website_content(url) for url in valid_urls])
                st.session_state.ideas = generate_blog_ideas(website_contents, num_ideas, st.session_state.tone, st.session_state.length, st.session_state.model)
                st.success('¡Ideas para blogs generadas!')
                # st.rerun()
            else:
                st.error('Por favor, ingrese al menos una URL válida.')

# Main content area
if st.session_state.ideas:
    display_idea_cards()
else:
    st.warning('👈 Ingrese URLs y haga clic en "Generar Ideas" para comenzar!')