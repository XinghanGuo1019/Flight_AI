import ollama
import re
import gradio as gr
from concurrent.futures import ThreadPoolExecutor
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
from chromadb.config import Settings
from chromadb import Client
from langchain_community.vectorstores import Chroma

def generate_embedding(chunk):
  return embed_func.embed_query(chunk) 


def retrieve_context(question):
    # Retrieve relevant documents
    results = retriever.invoke(question)
    # Combine the retrieved content
    context = "\n\n".join([doc for doc in results])
    return context


def query_deepseek(question, context):
    # Format the input prompt
    formatted_prompt = f"Question: {question}\n\nContext: {context}"
    # Query DeepSeek-R1 using Ollama
    response = embed_func.chat(
        model="deepseek-r1:7b",
        messages=[{'role': 'user', 'content': formatted_prompt}]
    )
    # Clean and return the response
    response_content = response['message']['content']
    final_answer = re.sub(r'<think>.*?</think>', '', response_content, flags=re.DOTALL).strip()
    return final_answer

def ask_question(question):
    # Retrieve context and generate an answer using RAG
    context = retrieve_context(question)
    answer = query_deepseek(question, context)
    return answer
# Set up the Gradio interface


# pdf_loader = PyMuPDFLoader("./RAG_Example.pdf")
# pdf_content = pdf_loader.load()
text_content = "Trupm is this year 69 years old."
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_text(text_content)
embed_func = OllamaEmbeddings(model="deepseek-r1:1.5b")

# with ThreadPoolExecutor() as executor:
#   embeddings = list(executor.map(generate_embedding, chunks))

client = Client(Settings())
if "foundation_of_llm" in [coll.name for coll in client.list_collections()]:
   client.delete_collection(name="foundation_of_llm")
else:
  collection = client.create_collection(name="foundation_of_llm")

documents = []
metadatas = []
ids = []
embedding_tab = []
for idx, chunk in enumerate(chunks):
  documents.append(chunk)
  metadatas.append({"id": idx})
  ids.append(str(idx))
  collection.add(
    documents=documents,
    metadatas=metadatas,
    embeddings=[generate_embedding(chunk)],
    ids=ids 
  )
retriever = Chroma(collection_name="foundations_of_llms", client=client, embedding_function=embed_func).as_retriever()


interface = gr.Interface(
    fn=ask_question,
    inputs="text",
    outputs="text",
    title="RAG Chatbot: Foundations of LLMs",
    description="Ask any question about the Foundations of LLMs book. Powered by DeepSeek-R1."
)
interface.launch()
