from langchain.document_loaders import PyPDFLoader
from langchain.llms import GooglePalm
from langchain.embeddings import HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import os
from fastapi import FastAPI, File, UploadFile, HTTPException,Request
from fastapi_async_langchain.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import glob
app = FastAPI()

# Mount the "static" directory to serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
load_dotenv()
current_dir = os.getcwd()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
llm = GooglePalm(google_api_key = os.environ["api_key"], temperature=0.1)
    
instructor_embeddings = HuggingFaceInstructEmbeddings(
                model_name = 'sentence-transformers/all-MiniLM-L6-v2'
    )

@app.post("/upload")
async def upload_pdf(pdf: UploadFile = File(...)):
    # `pdf` is of type `UploadFile`, which provides file information and access to its contents.
    # Save the file to a specific directory (e.g., 'uploads') on the server.
    global chain
    save_path = f"{current_dir}/{pdf.filename}"
    
    with open(save_path, "wb") as pdf_file:
        pdf_file.write(pdf.file.read())
    
    list_of_files = glob.glob(current_dir+'/*.pdf') # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getctime)

    loader = PyPDFLoader(latest_file)
    pages = loader.load_and_split()
    vectordb = FAISS.from_documents(documents=pages,embedding=instructor_embeddings)
    retriever = vectordb.as_retriever()
    prompt_template = """You are a legal expert. Given the following context and a question, generate an answer \
    based on the context only. You are required to understand the context very adeptly to answer the question. \
    The answer should be understandable to a layperson who do not have experience in reading leagal documents. \
    If the answer is not found in the context, kindly state \
    "I don't know." Don't try to make up an answer.

    CONTEXT: {context}

    QUESTION: {question}"""
    PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )
    chain = RetrievalQA.from_chain_type(llm=llm,
                chain_type = "stuff",
                retriever = retriever,
                input_key = 'query',
                return_source_documents = True,
                chain_type_kwargs={"prompt": PROMPT})
    return {"message": f"File '{pdf.filename}' has been saved successfully."}



@app.post("/ask")
async def ask_question(request: Request):
    global chain
    try:
        data = await request.json()
        question = data.get('question', '')
        print('='*50, question)
        if not question:
            raise HTTPException(status_code=400, detail="Question not provided")
        print('-'*50)
        response_result = chain(question)['result']
        response_data = {"question": question, "response": response_result, "status": "success"}

        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "*",
        }

        return JSONResponse(content=response_data, headers=headers)

    except Exception as e:
        print("Error:", e)
        return JSONResponse(content={"error": "Internal Server Error"}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
