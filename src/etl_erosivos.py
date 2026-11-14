import os
import pandas as pd
import numpy as np

def processar_erosivos():
    print("[ETL Erosivos] Iniciando processamento da base...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(base_dir, "../data/erosivos.csv")
    
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
    # Pula as 17 primeiras linhas de metadados e cabeçalho descritivo do IBGE
    df = pd.read_csv(caminho_arquivo, header=None, skiprows=17, sep=';', encoding='utf-8-sig', low_memory=False, dtype=str)
    
    # Renomeia as colunas dinamicamente
    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    
    # Filtra apenas as linhas que contêm o formato "Cidade (UF)" na coluna 0 (exclui o resumo "Brasil")
    df = df[df['col_0'].str.contains(r'\(.*\)', regex=True)].copy()
    
    # Extrai o Nome da Cidade e a UF usando Expressão Regular
    extracao = df['col_0'].str.extract(r'^(.*?)\s*\(([^)]+)\)')
    
    df_final = pd.DataFrame()
    df_final['nome_cidade'] = extracao[0].str.strip().str.title()
    df_final['uf'] = extracao[1].str.strip().str.upper()
    
    # Identifica a coluna de valor (coluna 1 com o valor total de ocorrências ou traço)
    col_valor = 'col_1' if 'col_1' in df.columns else df.columns[1]
    
    # Limpa valores numéricos (substitui traços '-', vírgulas e nulos por 0)
    df_final['total_processos_erosivos'] = df[col_valor].astype(str).str.replace('-', '0', regex=False)
    df_final['total_processos_erosivos'] = df_final['total_processos_erosivos'].str.replace(',', '.', regex=False)
    df_final['total_processos_erosivos'] = pd.to_numeric(df_final['total_processos_erosivos'], errors='coerce').fillna(0)
    
    # Remove eventuais linhas nulas
    df_final = df_final.dropna(subset=['nome_cidade', 'uf'])
    
    print(f"[ETL Erosivos] Sucesso! {len(df_final)} municípios processados.")
    return df_final

if __name__ == "__main__":
    df_resultado = processar_erosivos()
    
    print("\n" + "="*50)
    print("🔍 TESTE VISUAL: PROCESSOS EROSIVOS (PRIMEIRAS 10 CIDADES)")
    print("="*50)
    print(df_resultado.head(10).to_string(index=False))
    print("="*50)