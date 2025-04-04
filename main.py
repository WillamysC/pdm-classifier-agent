# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel
import uuid
import logging
import os


from services.rag_service import RagService
from models import *
from config import Settings
from logging_config import logger



# Load settings
settings = Settings()

# Initialize services
rag_service = RagService(settings)

class UploadResponse(BaseModel):
    file_id: str
    filename: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inciliaiza recursos da aplicação e encerra ao final"""
    logger.info("Inicializando recursos da aplicação...")
    try:
        await rag_service.initialize()
        logger.info("Recursos inicializados com sucesso")
    except Exception as e:
        logger.error(f"Falha na inicialização: {str(e)}")
    yield
    logger.info("Encerrando aplicação...")

app = FastAPI(
    title="PDM Classifier API", 
    description="API para classificação de PDMs usando técnicas de RAG",
    version="1.1.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload-descriptions/", response_model=UploadResponse)
async def upload_descriptions(file: UploadFile):
    """Upload and store descriptions file"""
    try:
        file_id = str(uuid.uuid4())
        # filename = f"{file_id}_{file.filename}"
        filename = f"{file_id}.xlsx"
        # file_path = os.path.join("uploads", f"{file_id}_{file.filename}")
        # file_path = os.path.join("uploads", f"{file_id}_")
        file_path = os.path.join("uploads", filename)

        
        os.makedirs("uploads", exist_ok=True)

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return UploadResponse(file_id=file_id, filename=file.filename)
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File upload failed. {str(e)}")

@app.post("/process-items/", response_model=ProcessResponse)
async def process_items(request: ProcessRequest):
    """Process items and return PDM classifications"""
    try:
        results = await rag_service.classify_descriptions(
            request.file_id,
            request.sample_size,
            request.similarity_threshold,
            request.llm_model
        )
        return ProcessResponse(response=results)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Processing failed")

@app.post("/process-single/", response_model=ProcessSingleResponse)
async def process_single_item(request: SingleDescriptionRequest):
    """Processa uma única descrição e retorna a classificação PDM"""
    try:
        result = await rag_service.classify_single_description(request.description)
        response =  ProcessSingleResponse(response=result)

        return response
    
    except Exception as e:
        logger.error(f"Processamento único falhou: {str(e)}")
        raise HTTPException(status_code=500, detail="Falha ao processar a descrição")

@app.post("/process-description/", response_model=ProcessSingleResponseN8n)
async def process_single_item(request: SingleDescriptionRequest):
    """Processa uma única descrição e retorna a classificação PDM"""
    try:
        result = await rag_service.select_possible_pdms_for_description(request.description)
        
        response = ProcessSingleResponseN8n(response=result)

        await send_to_n8n(response)

        return response
    
    except Exception as e:
        logger.error(f"Processamento único falhou: {str(e)}")
        raise HTTPException(status_code=500, detail="Falha ao processar a descrição")


async def send_to_n8n(data):
    """Função auxiliar para enviar dados para o n8n"""
    n8n_webhook_url = "http://localhost:5678/webhook-test/process-pdm"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                n8n_webhook_url,
                json=data.model_dump(),  # Converte o modelo Pydantic para um dicionário
                timeout=10.0  # Timeout para não bloquear muito tempo
            )
            
        if response.status_code != 200:
            logger.error(f"Falha ao enviar para n8n: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"Erro ao enviar dados para n8n: {str(e)}")
        # Não levanta exceção aqui para não afetar a resposta original

@app.get("/download-results/")
async def download_results(file_id: str):
    """Download results as Excel file"""
    file_path = os.path.join("results", f"{file_id}_results.xlsx")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Results not found")
    
    return FileResponse(
        path=file_path,
        filename="classification_results.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)