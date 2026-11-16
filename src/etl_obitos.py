import os
import pandas as pd
import numpy as np

def processar_obitos(caminho_csv):
    print(f"\n--- Processando: {os.path.basename(caminho_csv)} ---")
    
    df = pd.read_csv(caminho_csv, header=None, skiprows=9, sep=';', encoding='latin1', low_memory=False, dtype=str)
    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    
    extracao = df['col_0'].str.extract(r'^(.*?)\s*\(([^)]+)\)')
    df['nome_cidade'] = extracao[0].str.strip().str.title()
    df['uf'] = extracao[1].str.strip().str.upper()
    
    colunas_para_somar = [col for col in df.columns if col not in ['col_0', 'nome_cidade', 'uf']]
    
    for col in colunas_para_somar:
        df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    df['total_obitos'] = df[colunas_para_somar].sum(axis=1)
    
    df_final = df[['nome_cidade', 'uf', 'total_obitos']].copy()
    df_final = df_final.dropna(subset=['nome_cidade', 'uf'])
    
    print(f"   - Linhas válidas extraídas: {len(df_final)}")
    return df_final


def rodar_etl_obitos():
    """
    Processa e consolida as bases de óbitos seguindo o contrato padrão de saída:
    [nome_cidade, uf, total_obitos]
    """
    print("[ETL Óbitos] Iniciando processamento e unificação das bases...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_1 = os.path.join(base_dir, "../data/obitos_1.csv")
    caminho_2 = os.path.join(base_dir, "../data/obitos_2.csv")
    caminho_3 = os.path.join(base_dir, "../data/obitos_3.csv")
    
    for caminho in [caminho_1, caminho_2, caminho_3]:
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
            
    df1 = processar_obitos(caminho_1)
    df2 = processar_obitos(caminho_2)
    df3 = processar_obitos(caminho_3)
    
    print("\n -> Consolidando as bases (empilhamento)...")
    df_consolidado = pd.concat([df1, df2, df3], ignore_index=True)
    
    # Agrupamento padronizado
    df_consolidado = df_consolidado.groupby(['nome_cidade', 'uf'], as_index=False)['total_obitos'].sum()
    print(f"   - Total de registros únicos após agrupamento: {len(df_consolidado)}")
    
    print(f"[ETL Óbitos] Processamento concluído com sucesso!\n")
    return df_consolidado


if __name__ == "__main__":
    df_resultado = rodar_etl_obitos()
    print("="*50)
    print("🔍 TESTE VISUAL: ÓBITOS")
    print("="*50)
    print(df_resultado.head(10).to_string(index=False))
    print("="*50)