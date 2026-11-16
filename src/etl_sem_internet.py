import os
import pandas as pd
import numpy as np

def processar_sem_internet():
    print("[ETL Sem Internet] Iniciando processamento da base...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(base_dir, "../data/sem_internet.csv")
    
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
    # Pula as 18 primeiras linhas de metadados e cabeçalho descritivo
    df = pd.read_csv(caminho_arquivo, header=None, skiprows=18, sep=';', encoding='utf-8-sig', low_memory=False, dtype=str)
    
    # Renomeia as colunas para facilitar a manipulação
    df.columns = ['localidade', 'grupo_idade', 'total_moradores', 'sem_internet'][:len(df.columns)]
    
    # Limpa valores numéricos
    for col in ['total_moradores', 'sem_internet']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # Filtra apenas as linhas que representam o 'Total' por localidade
    df_filtrado = df[df['grupo_idade'].str.strip().str.lower() == 'total'].copy()
    
    # Mantém apenas as linhas que possuem o formato "Cidade (UF)" na coluna de localidade
    df_filtrado = df_filtrado[df_filtrado['localidade'].str.contains(r'\(.*\)', regex=True)].copy()
    
    # Extrai o Nome da Cidade e a Sigla da UF usando Expressão Regular
    extracao = df_filtrado['localidade'].str.extract(r'^(.*?)\s*\(([^)]+)\)')
    
    df_final = pd.DataFrame()
    df_final['nome_cidade'] = extracao[0].str.strip().str.title()
    df_final['uf'] = extracao[1].str.strip().str.upper()
    df_final['total_sem_internet'] = df_filtrado['sem_internet'].values
    
    # Calcula a % da população que não possui internet
    total_moradores = df_filtrado['total_moradores'].values
    df_final['pct_sem_internet'] = np.where(
        total_moradores > 0, 
        (df_filtrado['sem_internet'].values / total_moradores) * 100, 
        0.0
    ).round(2)
    
    # Remove eventuais nulos
    df_final = df_final.dropna(subset=['nome_cidade', 'uf'])
    
    print(f"[ETL Sem Internet] Sucesso! {len(df_final)} municípios processados.")
    return df_final

if __name__ == "__main__":
    df_resultado = processar_sem_internet()
    
    print("\n" + "="*50)
    print("🔍 TESTE VISUAL: SEM INTERNET (PRIMEIRAS 10 CIDADES)")
    print("="*50)
    print(df_resultado.head(10).to_string(index=False))
    print("="*50)