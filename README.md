# PDM Classifier Agent

Este projeto é uma API para classificação de PDMs (Padrões Descritivos de Materiais) utilizando técnicas de Recuperação de Informação e Geração de Linguagem Natural (RAG).

## Funcionalidades

- **Upload de Arquivos**: Permite o envio de arquivos Excel contendo descrições de itens.
- **Classificação de PDMs**: Processa descrições de itens e retorna os PDMs mais adequados.
- **Processamento de Descrição Única**: Classifica uma única descrição de item.
- **Integração com n8n**: Envia os resultados para um webhook configurado no n8n.
- **Download de Resultados**: Permite o download dos resultados processados em formato Excel.

## Requisitos

- Python 3.12 ou superior
- Dependências listadas no arquivo `pyproject.toml`

## Instalação

1. Clone o repositório:
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd pdm-classifier-agent
2. Instale as dependências utilizando o gerenciador de dependências uv:
    ```bash 
    uv install
3. Configure as variáveis de ambiente no arquivo ```.env```:
    ```bash 
    GROQ_API_KEY=<sua_chave_groq>
    GOOGLE_API_KEY=<sua_chave_google>
4. Crie um pasta de ```logs``` na raiz do projeto com dois arquivos ```.log```:
    ```
    app.log
    erros.log
    ```

## Uso
**Executar o Servidor**  
Inicie o servidor FastAPI:   
```
uvicorn main:app --reload
```

O servidor estará disponível em `http://127.0.0.1:8000`.


**Endpoints Principais**  
`POST /upload-descriptions/`: Faz upload de um arquivo Excel contendo descrições de itens.  
`POST /process-items/`: Processa descrições de itens e retorna os PDMs classificados.  
`POST /process-single/`: Processa uma única descrição e retorna o PDM mais adequado.  
`GET /download-results/`: Faz o download dos resultados processados.  