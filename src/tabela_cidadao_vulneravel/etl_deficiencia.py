import os
import pandas as pd
import numpy as np

def processar_deficiencia():
    """
    Processa a base de deficiência seguindo o contrato padrão de saída:
    [nome_cidade, uf, total_deficientes, total_mulheres]
    """
    print("[ETL Deficiência] Iniciando processamento da base...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(base_dir, "../../data/cidadao/deficiencia.csv")
    
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
    # Lê a base pulando as 5 primeiras linhas de metadados do IBGE
    df = pd.read_csv(
        caminho_arquivo, 
        header=None, 
        skiprows=5, 
        sep=';', 
        encoding='utf-8-sig', 
        low_memory=False, 
        dtype=str
    )
    
    # Renomeia as colunas com base na estrutura real da tabela:
    # col_0: Município | col_1: Total de Deficientes | col_2: Mulheres com Deficiência
    df = df.iloc[:, :3].copy()
    df.columns = ['localidade', 'total_deficientes', 'total_mulheres']
    
    # Filtra apenas as linhas que contêm o formato "Cidade (UF)" (exclui Brasil e Estados)
    df = df[df['localidade'].str.contains(r'\(.*\)', regex=True)].copy()
    
    # Extrai o Nome da Cidade e a UF usando Expressão Regular
    extracao = df['localidade'].str.extract(r'^(.*?)\s*\(([^)]+)\)')
    df['nome_cidade'] = extracao[0].str.strip().str.title()
    df['uf'] = extracao[1].str.strip().str.upper()
    
    # Limpa e converte as colunas numéricas
    for col in ['total_deficientes', 'total_mulheres']:
        df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
    # Monta o DataFrame final com o contrato exigido
    df_final = df[['nome_cidade', 'uf', 'total_deficientes', 'total_mulheres']].copy()
    
    # Remove nulos e garante unicidade por município/UF
    df_final = df_final.dropna(subset=['nome_cidade', 'uf'])
    df_final = df_final.groupby(['nome_cidade', 'uf'], as_index=False)[['total_deficientes', 'total_mulheres']].sum()
    
    print(f"[ETL Deficiência] Sucesso! {len(df_final)} municípios processados.")
    return df_final

if __name__ == "__main__":
    df_resultado = processar_deficiencia()
    print("\n" + "="*60)
    print("🔍 TESTE VISUAL: DEFICIÊNCIA POR MUNICÍPIO")
    print("="*60)
    print(df_resultado.head(10).to_string(index=False))
    print("="*60)