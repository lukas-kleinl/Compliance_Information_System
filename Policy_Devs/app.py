import gridfs
from flask import Flask, request, abort
from flask.cli import load_dotenv
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymongo.mongo_client import MongoClient
from langchain_community.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
import os

app = Flask(__name__)

load_dotenv()
uri = os.getenv("MongoDB_URI")
client = MongoClient(uri)
db = client.company_controls
OPENAI_API_KEY = os.getenv("AUTH0_CLIENT_ID")
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
llm = Ollama(model="llama2", callback_manager=callback_manager)
fs = gridfs.GridFS(db)

collection_policy = db["policy"]
collection_guideline = db["guideline"]

guideline_data = collection_guideline.find()
policy_data = collection_policy.find()

files = []
for policy in policy_data:
    files.append(fs.get(policy["file"]["file"]))

for guideline in guideline_data:
    files.append(fs.get(guideline["file"]["file"]))

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
page_loader = None
for file in files:
    #need to create local file cause PyPDF Loader cant handle BytesIO
    filename = file.filename
    with open(f"./static/{filename}.pdf", "wb") as f:
        f.write(file.read())
        loader = PyPDFLoader(f"./static/{filename}.pdf")
        pages = loader.load()
        pages = text_splitter.split_documents(pages)
        if page_loader is None:
            page_loader = pages
        else:
            page_loader += pages

new_collection = db["Chat_Search"]

vectorstore = MongoDBAtlasVectorSearch.from_documents(documents=page_loader,
                                                      embedding=OpenAIEmbeddings(disallowed_special=()),
                                                      #OpenAI 1536 indices, OllamaEmbeddings(),(4096)
                                                      collection=new_collection, index_name="vector_index")

vectorstore_chat = MongoDBAtlasVectorSearch.from_documents(documents=page_loader,
                                                           embedding=OpenAIEmbeddings(disallowed_special=()),
                                                           collection=new_collection, index_name="vector_index")

prompt = """
    Use the following context to answer the question.
    Only use the knowledge provided by the documents.
    Do not answer any questions out of the provided knowledge.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    {context}
    Question: {question}
    Helpful Answer:"""

QA_CHAIN_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=prompt,
)

qa_chain = RetrievalQA.from_chain_type(
    llm,
    retriever=vectorstore_chat.as_retriever(),
    chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
)


@app.before_request
def limit_remote_addr():
    if request.remote_addr != '127.0.0.1':
        abort(403)  # Forbidden


@app.route('/query')
def process_query():
    question = str(request.args.get('question'))
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 1})
    results = retriever.invoke(question)
    try:
        result = results[0].page_content
        source = results[0].metadata["source"]
        page = results[0].metadata["page"]
        result += "\nDocument: " + source + " on page " + str(page)
    except IndexError:
        return "error while retrieving information from vector search", 404

    return {"query": question, "result": result}


@app.route('/chat')
def process_chat():
    question = str(request.args.get('question'))
    result = qa_chain({"query": question})
    return result


if __name__ == '__main__':
    app.run()
