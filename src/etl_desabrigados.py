import os
import pandas as pd
import numpy as np

def processar_arquivo_individual(caminho_csv):
    print(f"\n--- Processando: {os.path.basename(caminho_csv)} ---")
    
    # Lê o arquivo ignorando os metadados iniciais e mapeando sem cabeçalho fixo
    df = pd.read_csv(caminho_csv, header=None, skiprows=9, sep=';', encoding='utf-8-sig', low_memory=False, dtype=str)
    
    # Renomeia as colunas dinamicamente
    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    
    # A Coluna 0 contém o Município e a UF (ex: "Abatiá (PR)")
    extracao = df['col_0'].str.extract(r'^(.*?)\s*\(([^)]+)\)')
    df['nome_cidade'] = extracao[0].str.strip().str.title()
    df['nome_uf'] = extracao[1].str.strip().str.upper()
    
    # Seleciona todas as colunas numéricas de dados (da coluna 1 em diante)
    colunas_para_somar = [col for col in df.columns if col not in ['col_0', 'nome_cidade', 'nome_uf']]
    
    for col in colunas_para_somar:
        # Substitui vírgula por ponto, converte traços '-' ou nulos em 0 e transforma em número
        df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    # Soma todas as colunas de desabrigados/desalojados em uma única coluna final
    df['total_desabrigados'] = df[colunas_para_somar].sum(axis=1)
    
    # Mantém apenas o formato final desejado e remove linhas inválidas
    df_final = df[['nome_cidade', 'nome_uf', 'total_desabrigados']].copy()
    df_final = df_final.dropna(subset=['nome_cidade', 'nome_uf'])
    
    print(f"   - Linhas válidas extraídas: {len(df_final)}")
    return df_final


def rodar_etl_desabrigados():
    print("[ETL Desabrigados] Iniciando processamento e unificação das 3 bases...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Caminhos para os arquivos de desabrigados na pasta data/
    caminho_1 = os.path.join(base_dir, "../data/desabrigados_1.csv")
    caminho_2 = os.path.join(base_dir, "../data/desabrigados_2.csv")
    caminho_3 = os.path.join(base_dir, "../data/desabrigados_3.csv")
    
    for caminho in [caminho_1, caminho_2, caminho_3]:
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
            
    df1 = processar_arquivo_individual(caminho_1)
    df2 = processar_arquivo_individual(caminho_2)
    df3 = processar_arquivo_individual(caminho_3)
    
    print("\n -> Consolidando as bases (empilhamento)...")
    df_consolidado = pd.concat([df1, df2, df3], ignore_index=True)
    
    # Agrupa por cidade e UF somando os valores de desabrigados, sem duplicar municípios
    df_consolidado = df_consolidado.groupby(['nome_cidade', 'nome_uf'], as_index=False)['total_desabrigados'].sum()
    print(f"   - Total de registros únicos na base consolidada: {len(df_consolidado)}")
    
    print(f"[ETL Desabrigados] Processamento concluído com sucesso!\n")
    return df_consolidado


if __name__ == "__main__":
    df_resultado = rodar_etl_desabrigados()
    
    print("="*50)
    print("🔍 TESTE VISUAL: PRIMEIRAS 10 LINHAS DA BASE DE DESABRIGADOS")
    print("="*50)
    print(df_resultado.head(10).to_string(index=False))
    print("="*50)
    print(f"📊 Total de registros na tabela final: {len(df_resultado)}")