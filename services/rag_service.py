# services/rag_service.py
import asyncio
import os
import time
import pandas as pd
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnableParallel
from typing import List, Dict
from pdm_filter import filter_pdms
from config import Settings
import logging
import glob
from logging_config import logger
# logger = logging.getLogger(__name__)

class RagService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pdms_df = None
        self.llm_chain = None
        self.embedding_model = None

    async def initialize(self):
        """Load required resources"""
        await self._load_pdms()
        self._initialize_llm()
        
    async def _load_pdms(self):
        """Load and preprocess PDM data"""
        try:
            self.pdms_df = pd.read_excel(
                self.settings.pdm_file_path,
                usecols=['PDM']
            ).drop_duplicates()
            logger.info("Successfully loaded PDM data")
        except Exception as e:
            logger.error(f"Failed to load PDM data: {str(e)}")
            raise

    def _initialize_llm(self):
        """Initialize LLM chain"""
        template = """..."""  # Your existing template here
        
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Você é um analista de dados, trabalhando em um projeto de MDM (Master Data Management).
                    Seu trabalho é escolher um PDM (padrão descritivo de materiais) adequado para cada descrição de material que vou te enviar.

                    Todas são descricões de uma base de itens de um cliente X.
                    
                    Escolha um dentre os seguintes PDMs:
                    {pdms}
                    """,
                ),
                ("human", """
                Escolha o PDM deste item:
                {item}

                Responda apenas com o PDM.
                """),
            ]
        )
        # self.llm = ChatGroq(
        #     model_name=self.settings.default_llm_model,
        #     api_key=self.settings.groq_api_key
        # )
        self.llm = ChatGoogleGenerativeAI(
            model=self.settings.google_llm_model,  # Changed from model_name
            google_api_key=self.settings.google_api_key,  # Specific parameter name
            temperature=0.1
        )
        self.llm_chain = prompt | self.llm

    async def classify_single_description(self, description: str) -> Dict:
        """
        Classifica uma única descrição e retorna o PDM mais adequado.
        
        Args:
            description (str): A descrição do item para classificar
            
        Returns:
            Dict: Dicionário contendo o PDM selecionado, PDMs filtrados e confiança
        """
        try:
            pdms_filtrados = await asyncio.to_thread(filter_pdms, description, self.pdms_df)
            
            input_data = {
                "pdms": ", ".join([pdm for pdm, _ in pdms_filtrados]),
                "item": description
            }
            
            response = await self.llm_chain.ainvoke(input_data)
            
            selected_pdm = response.content.replace('\n', '')
            
            confidence = next((score for pdm, score in pdms_filtrados if pdm == selected_pdm), None)
            
            return {
                "id_level": None,  # ID não é aplicável para uma única descrição
                "item_description": description,
                "selected_pdm": selected_pdm,
                "filtered_pdms": [pdm for pdm, _ in pdms_filtrados],
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"Erro ao classificar descrição única: {str(e)}")
            raise
    
    async def select_possible_pdms_for_description(self, description: str) -> Dict:
        """
        Classifica uma única descrição e retorna o PDM mais adequado.
        
        Args:
            description (str): A descrição do item para classificar
            
        Returns:
            Dict: Dicionário contendo o PDM selecionado, PDMs filtrados e confiança
        """
        try:
            pdms_filtrados = await asyncio.to_thread(filter_pdms, description, self.pdms_df)
            
            input_data = {
                "pdm_score": {pdm: score for pdm, score in pdms_filtrados},
                "pdms": ", ".join([pdm for pdm, _ in pdms_filtrados]),
                "description": description
            }
                            
            return input_data
        
        except Exception as e:
            logger.error(f"Erro ao classificar descrição única: {str(e)}")
            raise

    async def classify_descriptions(self, file_id: str, sample_size: int,
                                 similarity_threshold: float, model: str, chunk_size: int = 5,) -> List[Dict]:
        """Process descriptions with RAG pipeline"""
        try:
            # Load descriptions
            pattern = os.path.join("uploads", f"{file_id}.xlsx") 
            matching_files = glob.glob(pattern)
        
            if not matching_files:
                raise FileNotFoundError(f"No files found with ID: {file_id}")
                
            if len(matching_files) > 1:
                raise ValueError(f"Multiple files found for ID: {file_id}")
                
            file_path = matching_files[0]
            descriptions_df = pd.read_excel(file_path, usecols='A, B')
            
            # Sample items
            sample_df = descriptions_df.sample(n=sample_size)
            
            # Process items
            results = []

            dfs = []
            for i in range(0, len(sample_df), chunk_size):
                try:
                    batch = sample_df.iloc[i:i+chunk_size].copy()
                    print(f"Processing batch {i}: size {len(batch)}")
                    descricoes = batch['DESCRICOES']
                    Ids = batch['ID']

                    pdms_filtrados = await asyncio.gather(*[
                        asyncio.to_thread(filter_pdms, desc, self.pdms_df) 
                        for desc in batch['DESCRICOES']
                    ])

                    inputs = [{
                        "pdms": ", ".join([pdm for pdm, _ in pdms]),
                        "item": desc
                        } for pdms, desc in zip(pdms_filtrados, descricoes)]
                    
                    responses = await self.llm_chain.abatch(inputs)

                    for response, pdms, desc, id in zip(responses, pdms_filtrados, descricoes, Ids):
                        selected_pdm = response.content.replace('\n', '')
                        confidence = next((score for pdm, score in pdms if pdm == selected_pdm), None)
                        
                        results.append({
                            'id_level': id,
                            "item_description": desc,
                            "selected_pdm": selected_pdm,
                            "confidence": confidence,
                            "filtered_pdms": [pdm for pdm, _ in pdms]
                        })

                    time.sleep(30)
                except Exception as e:
                    print(f"Error on batch {i}: {e}")
                    time.sleep(10)  # Wait 10 seconds before retrying
            
            # Save results
            # self._save_results(results, file_id)
            return results
            
        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            raise

    def _save_results(self, results: List[Dict], file_id: str):
        """Save results to Excel"""
        os.makedirs("results", exist_ok=True)
        df = pd.DataFrame(results)
        df.to_excel(f"results/{file_id}_results.xlsx", index=False)
