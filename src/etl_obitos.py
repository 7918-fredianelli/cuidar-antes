import os
import pandas as pd
import numpy as np

def processar_arquivo_individual(caminho_csv):
    print(f"\n--- Processando: {os.path.basename(caminho_csv)} ---")
    
    # skiprows=9 pula os metadados e a linha de cima do cabeçalho duplo. 
    # Começa direto na linha 10, onde os dados de Alta Floresta D'Oeste começam.
    df = pd.read_csv(caminho_csv, header=None, skiprows=9, sep=';', encoding='latin1', low_memory=False, dtype=str)
    
    # Renomeia as colunas explicitamente com base na estrutura real do arquivo:
    # Coluna 0: Município
    # Colunas 1 a 6: Anos e categorias (2017, 2018, 2019, 2020, Não sabe, Não possui informação, etc.)
    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    
    # A Coluna 0 contém o Município e a UF (ex: "Alta Floresta D'Oeste (RO)")
    extracao = df['col_0'].str.extract(r'^(.*?)\s*\(([^)]+)\)')
    df['nome_cidade'] = extracao[0].str.strip().str.title()
    df['nome_uf'] = extracao[1].str.strip().str.upper()
    
    # Seleciona todas as colunas de dados numéricos (da coluna 1 em diante)
    colunas_para_somar = [col for col in df.columns if col != 'col_0' and col != 'nome_cidade' and col != 'nome_uf']
    
    for col in colunas_para_somar:
        # Substitui vírgula por ponto, converte traços '-' ou nulos em 0 e transforma em número
        df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    # Soma todas as colunas de óbitos em uma única coluna final
    df['total_obitos'] = df[colunas_para_somar].sum(axis=1)
    
    # Mantém apenas o formato final desejado
    df_final = df[['nome_cidade', 'nome_uf', 'total_obitos']].copy()
    
    # Remove linhas vazias ou linhas de rodapé/cabeçalho que não tenham cidade ou UF
    df_final = df_final.dropna(subset=['nome_cidade', 'nome_uf'])
    
    print(f"   - Linhas válidas extraídas: {len(df_final)}")
    print("   - Exemplo das 2 primeiras cidades deste arquivo:")
    print(df_final.head(2).to_string(index=False))
    
    return df_final


def rodar_etl_obitos():
    print("[ETL Óbitos] Iniciando processamento e unificação das 3 bases...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    caminho_1 = os.path.join(base_dir, "../data/obitos_1.csv")
    caminho_2 = os.path.join(base_dir, "../data/obitos_2.csv")
    caminho_3 = os.path.join(base_dir, "../data/obitos_3.csv")
    
    for caminho in [caminho_1, caminho_2, caminho_3]:
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
            
    df1 = processar_arquivo_individual(caminho_1)
    df2 = processar_arquivo_individual(caminho_2)
    df3 = processar_arquivo_individual(caminho_3)
    
    print("\n -> Consolidando as bases (empilhamento)...")
    df_consolidado = pd.concat([df1, df2, df3], ignore_index=True)
    print(f"   - Total de linhas empilhadas: {len(df_consolidado)}")
    
    # Agrupa por cidade e UF somando os óbitos (caso os arquivos tenham os mesmos municípios)
    df_consolidado = df_consolidado.groupby(['nome_cidade', 'nome_uf'], as_index=False)['total_obitos'].sum()
    print(f"   - Total de registros únicos após agrupamento por cidade/UF: {len(df_consolidado)}")
    
    print(f"[ETL Óbitos] Processamento concluído com sucesso!\n")
    return df_consolidado


if __name__ == "__main__":
    df_resultado = rodar_etl_obitos()
    
    print("="*50)
    print("🔍 TESTE VISUAL: PRIMEIRAS 10 LINHAS DA BASE DE ÓBITOS")
    print("="*50)
    print(df_resultado.head(10).to_string(index=False))
    print("="*50)
    print(f"📊 Total de registros na tabela final: {len(df_resultado)}")