import streamlit as st
from streamlit_chat import message
from langchain.chains import ConversationalRetrievalChain
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.embeddings import HuggingFaceEmbeddings,OpenAIEmbeddings
from langchain.llms import CTransformers
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv
# Function to load documents


def load_documents():
    print('Started to load documents')
    loader = DirectoryLoader('data/', glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    print('Documents loaded')
    return documents


# Function to split text into chunks
def split_text_into_chunks(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50)
    text_chunks = text_splitter.split_documents(documents)
    print ('Chunks created')
    return text_chunks

# Function to create embeddings


def create_embeddings():
    print('Embeddings started')
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': "cpu"})
    print('Embeddings done')
    return embeddings
# Function to create vector store

def make_vectorstore(text_chunks):
    load_dotenv()
    # embeddings = OpenAIEmbeddings()
    # test = np.load('savefile.npy',allow_pickle=True)
    # if (test):
    #     return test
    # embeddings = HuggingFaceInstructEmbeddings(model_name='hkunlp/instructor-xl')
    embeddings = OpenAIEmbeddings(deployment=os.getenv("OPENAI_DEPLOYMENT_NAME"),chunk_size=1,)
    print('Embedding started')
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding = embeddings)
    # vectorstore=FAISS.load_local('vectorstore',embeddings)
    print('Vector store received')
    vectorstore.save_local('Vectorstore')
    # vs = np.array(vectorstore)
    # np.save('savefile.npy',vs)
    return vectorstore

def create_vector_store(text_chunks, embeddings):
    vector_store = FAISS.from_documents(text_chunks, embeddings)
    return vector_store

# Function to create LLMS model


def create_llms_model():
    llm = CTransformers(model="mistral-7b-instruct-v0.1.Q4_K_M.gguf",
                        config={'max_new_tokens': 128, 'temperature': 0.01})
    return llm


# Initialize Streamlit app
st.title("AI research assistant")
st.markdown(
    '<style>h1{color: orange; text-align: center;}</style>', unsafe_allow_html=True)
st.subheader('Get help from the chatbot')
st.markdown(
    '<style>h3{color: pink; text-align: center;}</style>', unsafe_allow_html=True)

# loading of documents
documents = load_documents()

# Split text into chunks
text_chunks = split_text_into_chunks(documents)

# Create embeddings
embeddings = create_embeddings()


# Create vector store
vector_store = create_vector_store(text_chunks, embeddings)

# Create LLMS model
llm = create_llms_model()


# Initialize conversation history
if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'generated' not in st.session_state:
    st.session_state['generated'] = ["Hello! Ask me anything "]

if 'past' not in st.session_state:
    st.session_state['past'] = ["Hey! 👋"]

# Create memory
memory = ConversationBufferMemory(
    memory_key="chat_history", return_messages=True)

# Create chain
chain = ConversationalRetrievalChain.from_llm(llm=llm, chain_type='stuff',
                                              retriever=vector_store.as_retriever(
                                                  search_kwargs={"k": 2}),
                                              memory=memory)

# Define chat function


def conversation_chat(query):
    result = chain(
        {"question": query, "chat_history": st.session_state['history']})
    st.session_state['history'].append((query, result["answer"]))
    return result["answer"]


# Display chat history
reply_container = st.container()
container = st.container()

with container:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_input(
            "Question:", placeholder="Ask about your research", key='input')
        submit_button = st.form_submit_button(label='Send')

    if submit_button and user_input:
        output = conversation_chat(user_input)
        st.session_state['past'].append(user_input)
        st.session_state['generated'].append(output)

if st.session_state['generated']:
    with reply_container:
        for i in range(len(st.session_state['generated'])):
            message(st.session_state["past"][i], is_user=True, key=str(
                i) + '_user', avatar_style="thumbs")
            message(st.session_state["generated"][i],
                    key=str(i), avatar_style="fun-emoji")
