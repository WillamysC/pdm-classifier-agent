import re
import pandas as pd
import faiss
import unicodedata
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import normalize
from nltk.corpus import stopwords

# Modelo de embeddings semânticos
model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
# model = AutoModelForMaskedLM.from_pretrained("neuralmind/bert-base-portuguese-cased")

def preprocess(text):
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()
    
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    units = [
        'mm', 'cm', 'm', 'km', 'pol', 'polegadas', 'polegada', 'in', 'inch', 'ft', 'yd', 
        'mi', 'milhas', 'l', 'ml', 'cl', 'gal', 'oz', 'fl', 'g', 'kg', 'mg', 
        'lb', 'ton', 'v', 'vca', 'vdc', 'w', 'a', 'hz', 'kwh', 'un', 'und', 
        'pc', 'pcs', 'h', 'min', 's', 'sqft', 'sqm', 'cv', 'hp', 'rpm', 'mph',
        'kph', 'volts', 'watts', 'amps', 'ohms', 'gb', 'mb', 'tb', 'ppm', 'dpi',
        'kpa', 'psi', 'bar', 'ph', 'ah', 'rms', 'va', 'lm', 'lux', 'db', 'bit',
        'byte', 'cm³', 'm³', 'cm²', 'm²', 'kw', 'kva', 'wh', 'dia', 'dias',
        'semana', 'semanas', 'mes', 'meses', 'ano', 'anos', 'hr', 'hrs', 'bsp'
    ]
    stopword = list(set(stopwords.words("portuguese")))
    text = re.sub(r'\b(?:' + '|'.join(units + stopword) + r')\b', '', text)
    
    # Remove single/double-letter words (1-2 characters)
    text = re.sub(r'\b\w{1,2}\b', '', text)  # Updated regex

    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def filter_pdms(item: str, pdms: pd.DataFrame) -> list[str]:
    try:
        primeira_palavra = item.split()[0]
        # _pdms = pdms[pdms['PDM'].str.contains(item.split()[0])]['PDM'].tolist()
        _pdms = pdms[pdms['PDM'].str.contains(primeira_palavra, case=False, regex=False)]['PDM'].tolist()

        if not None in _pdms:
            pdms_processados = [preprocess(p) for p in _pdms]
            limiar = 0.3
        else:
            pdms_processados = [preprocess(p) for p in pdms]
            limiar = 0.6
            
        embeddings_pdms_lista = model.encode(pdms_processados)
        
        embeddings_pdms_lista = normalize(embeddings_pdms_lista, norm='l2', axis=1)
        
        dimension = embeddings_pdms_lista.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings_pdms_lista)
        

        descricao_processada = preprocess(item[:25])
        embedding_consulta = model.encode([descricao_processada[:25]])
        embedding_consulta = normalize(embedding_consulta, norm='l2', axis=1)
        
        k = 6
        distancias, indices = index.search(embedding_consulta, k)
        
        resultados = []
        for idx, score in zip(indices[0], distancias[0]):
            if score < limiar:
                continue
            resultados.append((_pdms[idx], score))
        
        # print(resultados)
        return resultados
    except Exception as e:
        print(f"Error processing item '{item}': {e}")
        return []

# if __name__ == "__main__":
#     pdms = pd.read_excel(r"G:\.shortcut-targets-by-id\1UwC7m1xfbSIiGfjl_jHzZz9GkeMnqpOE\CENTRAL CADASTRO\01. BASE LEVEL\BASE LEVEL PDM's _ Atualizado em 16.10 - Sem Caracteres Especiais (1).xlsx", usecols='D')
#     pdms = pdms.drop_duplicates()



#     item = 'CINTA ACO 3" ANEIS PISTAO 125-2'
#     # items = ["Bloco contatos p/bot.comand. Schneider", "Bobina 220Vca p/contator Telemec", "Botão comando puls/ilum. VD", "Transf.com. 1,0KVA 1F prim.480V"]
#     print(filter_pdms(item, pdms))