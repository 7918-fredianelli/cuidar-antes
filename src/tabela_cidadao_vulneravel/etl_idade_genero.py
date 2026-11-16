import os
import pandas as pd
import numpy as np

def processar_arquivo_idade_genero(caminho_csv):
    print(f"\n--- Processando: {os.path.basename(caminho_csv)} ---")
    
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_csv}")
        
    # Lê os dados a partir da linha 9 (skiprows=9), onde começam os municípios
    df = pd.read_csv(caminho_csv, header=None, skiprows=9, sep=';', encoding='utf-8-sig', low_memory=False, dtype=str)
    
    # Nomeia as colunas de forma genérica para garantir estabilidade no mapeamento por índice
    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    
    # Filtra apenas as linhas que contêm o formato "Cidade (UF)" (exclui Brasil e Estados)
    df = df[df['col_0'].str.contains(r'\(.*\)', regex=True)].copy()
    
    # Extrai o Nome da Cidade e a UF usando Expressão Regular
    extracao = df['col_0'].str.extract(r'^(.*?)\s*\(([^)]+)\)')
    df['nome_cidade'] = extracao[0].str.strip().str.title()
    df['uf'] = extracao[1].str.strip().str.upper()
    
    # Mapeamento exato das colunas de interesse conforme a estrutura do IBGE:
    # col_2 a col_7 -> Faixas etárias do total
    # col_8         -> Total de Mulheres (ignorando as quebras detalhadas de mulheres a partir de col_9)
    colunas_alvo = {
        'col_2': '0 a 4 anos',
        'col_3': '5 a 9 anos',
        'col_4': '10 a 14 anos',
        'col_5': '50 a 59 anos',
        'col_6': '60 a 69 anos',
        'col_7': '70 anos ou mais',
        'col_8': 'total_mulheres'
    }
    
    df_final = pd.DataFrame()
    df_final['nome_cidade'] = df['nome_cidade']
    df_final['uf'] = df['uf']
    
    for col_orig, nome_novo in colunas_alvo.items():
        if col_orig in df.columns:
            serie = df[col_orig].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df_final[nome_novo] = pd.to_numeric(serie, errors='coerce').fillna(0)
        else:
            df_final[nome_novo] = 0
            
    # Remove linhas vazias ou inválidas
    df_final = df_final.dropna(subset=['nome_cidade', 'uf'])
    
    print(f"   - Linhas válidas extraídas: {len(df_final)}")
    return df_final


def rodar_etl_idade_genero():
    """
    Processa e unifica as bases de idade e gênero, mantendo as faixas etárias e 
    adicionando a coluna consolidada 'total_mulheres'.
    """
    print("[ETL Idade e Gênero] Iniciando processamento e unificação das bases...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Caminho ajustado para a estrutura /data/cidadao/
    caminho_1 = os.path.join(base_dir, "../../data/cidadao/idade_genero_01.csv")
    caminho_2 = os.path.join(base_dir, "../../data/cidadao/idade_genero_02.csv")
    
    df1 = processar_arquivo_idade_genero(caminho_1)
    df2 = processar_arquivo_idade_genero(caminho_2)
    
    print("\n -> Consolidando as bases (empilhamento e soma por município)...")
    
    df_consolidado = pd.concat([df1, df2], ignore_index=True)
    
    colunas_valor = ['0 a 4 anos', '5 a 9 anos', '10 a 14 anos', '50 a 59 anos', '60 a 69 anos', '70 anos ou mais', 'total_mulheres']
    dicionario_agregacao = {col: 'sum' for col in colunas_valor if col in df_consolidado.columns}
    
    df_consolidado = df_consolidado.groupby(['nome_cidade', 'uf'], as_index=False).agg(dicionario_agregacao)
    
    print(f"   - Total de registros únicos após agrupamento: {len(df_consolidado)}")
    print(f"[ETL Idade e Gênero] Processamento concluído com sucesso!\n")
    
    return df_consolidado


if __name__ == "__main__":
    df_resultado = rodar_etl_idade_genero()
    print("="*100)
    print("🔍 TESTE VISUAL: AMOSTRA COM FAIXAS ETÁRIAS E 'total_mulheres'")
    print("="*100)
    print(df_resultado.head(10).to_string(index=False))
    print("="*100)