import os
import pandas as pd
import numpy as np

def processar_sem_internet():
    """
    Processa a base de sem internet seguindo o contrato padrão de saída:
    [nome_cidade, uf, total_sem_internet]
    """
    print("[ETL Sem Internet] Iniciando processamento da base...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(base_dir, "../data/sem_internet.csv")
    
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
    df = pd.read_csv(caminho_arquivo, header=None, skiprows=18, sep=';', encoding='utf-8-sig', low_memory=False, dtype=str)
    df.columns = ['localidade', 'grupo_idade', 'total_moradores', 'sem_internet'][:len(df.columns)]
    
    for col in ['total_moradores', 'sem_internet']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    df_filtrado = df[df['grupo_idade'].str.strip().str.lower() == 'total'].copy()
    df_filtrado = df_filtrado[df_filtrado['localidade'].str.contains(r'\(.*\)', regex=True)].copy()
    
    extracao = df_filtrado['localidade'].str.extract(r'^(.*?)\s*\(([^)]+)\)')
    
    df_final = pd.DataFrame()
    df_final['nome_cidade'] = extracao[0].str.strip().str.title()
    df_final['uf'] = extracao[1].str.strip().str.upper()
    df_final['total_sem_internet'] = df_filtrado['sem_internet'].values
    
    # Remove nulos e garante unicidade por município/UF
    df_final = df_final.dropna(subset=['nome_cidade', 'uf'])
    df_final = df_final.groupby(['nome_cidade', 'uf'], as_index=False)['total_sem_internet'].sum()
    
    print(f"[ETL Sem Internet] Sucesso! {len(df_final)} municípios processados.")
    return df_final

if __name__ == "__main__":
    df_resultado = processar_sem_internet()
    print("\n" + "="*50)
    print("🔍 TESTE VISUAL: SEM INTERNET")
    print("="*50)
    print(df_resultado.head(10).to_string(index=False))
    print("="*50)