import os
import pandas as pd
import numpy as np

def processar_alagamentos():
    """
    Processa a base de alagamentos seguindo o contrato padrão de saída:
    [nome_cidade, uf, total_alagamentos]
    """
    print("[ETL Alagamentos] Iniciando processamento da base...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(base_dir, "../../data/territorios/alagamentos.csv")
    
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
    # Pula as 15 primeiras linhas de metadados e cabeçalho do IBGE
    df = pd.read_csv(caminho_arquivo, header=None, skiprows=15, sep=';', encoding='utf-8-sig', low_memory=False, dtype=str)
    
    # Renomeia as colunas dinamicamente
    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    
    # Filtra apenas as linhas que contêm o formato "Cidade (UF)"
    df = df[df['col_0'].str.contains(r'\(.*\)', regex=True)].copy()
    
    # Extrai o Nome da Cidade e a UF usando Expressão Regular
    extracao = df['col_0'].str.extract(r'^(.*?)\s*\(([^)]+)\)')
    
    df_final = pd.DataFrame()
    df_final['nome_cidade'] = extracao[0].str.strip().str.title()
    df_final['uf'] = extracao[1].str.strip().str.upper()
    
    # Identifica a coluna de valor
    col_valor = 'col_2' if 'col_2' in df.columns else df.columns[-1]
    
    # Limpa valores numéricos (substitui traços '-', vírgulas e nulos por 0)
    df_final['total_alagamentos'] = df[col_valor].astype(str).str.replace('-', '0', regex=False)
    df_final['total_alagamentos'] = df_final['total_alagamentos'].str.replace(',', '.', regex=False)
    df_final['total_alagamentos'] = pd.to_numeric(df_final['total_alagamentos'], errors='coerce').fillna(0)
    
    # Remove eventuais linhas nulas e garante unicidade por município/UF
    df_final = df_final.dropna(subset=['nome_cidade', 'uf'])
    df_final = df_final.groupby(['nome_cidade', 'uf'], as_index=False)['total_alagamentos'].sum()
    
    print(f"[ETL Alagamentos] Sucesso! {len(df_final)} municípios processados.")
    return df_final

if __name__ == "__main__":
    df_resultado = processar_alagamentos()
    print("\n" + "="*50)
    print("🔍 TESTE VISUAL: ALAGAMENTOS")
    print("="*50)
    print(df_resultado.head(10).to_string(index=False))
    print("="*50)