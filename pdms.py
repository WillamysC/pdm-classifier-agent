from config import Settings
import pandas as pd

def carregar_pdms_do_excel(settings: Settings) -> dict:
    df = pd.read_excel(settings.pdm_file_path, usecols=['PDM', 'SEQ', 'ATRIBUTOS'])
    
    pdms = {}
    for _, row in df.iterrows():
        codigo_pdm = row['PDM']
        seq = row['SEQ']
        atributo = row['ATRIBUTOS']
        
        if codigo_pdm not in pdms:
            pdms[codigo_pdm] = []
        
        pdms[codigo_pdm].append({
            'sequencia': seq,
            'nome': atributo
        })
    
    for pdm in pdms:
        pdms[pdm] = sorted(pdms[pdm], key=lambda x: x['sequencia'])
        pdms[pdm] = [attr['nome'] for attr in pdms[pdm]]  # Simplifica para lista de nomes
        
    return pdms