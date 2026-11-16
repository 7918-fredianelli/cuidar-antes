import os
import pandas as pd

def processar_territorios():
    print("[ETL Territórios] Iniciando processamento da base de territórios...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(base_dir, "../data/territorios.csv")
    
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
    # Pula as 14 primeiras linhas de metadados do IBGE
    df = pd.read_csv(caminho_arquivo, header=None, skiprows=14, sep=';', encoding='utf-8-sig', low_memory=False, dtype=str)
    
    # Renomeia as colunas para facilitar o mapeamento
    # Geralmente a estrutura do IBGE traz: [0] Código UF, [1] Nome UF, [2] Código Município, [3] Nome Município (ajuste conforme a posição exata se necessário)
    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    
    # Mapeamento padrão IBGE para tabelas territoriais:
    # col_0: Código UF | col_1: Nome UF | col_2: Código Município | col_3: Nome do Município
    df_final = pd.DataFrame()
    df_final['codigo_uf'] = df['col_0'].str.strip()
    df_final['nome_uf'] = df['col_1'].str.strip()
    df_final['codigo_cidade'] = df['col_2'].str.strip()
    df_final['nome_cidade'] = df['col_3'].str.strip().str.title()
    
    # Adiciona a abreviação da cidade (ex: primeiras letras ou lógica customizada, mapeada aqui para a sigla padrão se aplicável)
    # Criando a abreviação padrão baseada nas iniciais ou nos primeiros caracteres do nome
    df_final['abreviacao_cidade'] = df_final['nome_cidade'].apply(lambda x: ''.join([w[0] for w in x.split()]).upper() if isinstance(x, str) else '')
    
    # Remove linhas vazias ou nulas
    df_final = df_final.dropna(subset=['codigo_cidade', 'nome_cidade'])
    
    print(f"[ETL Territórios] Sucesso! {len(df_final)} registros processados.")
    return df_final

if __name__ == "__main__":
    df_territorios = processar_territorios()
    
    print("\n" + "="*50)
    print("🔍 TESTE VISUAL: TERRITÓRIOS PROCESSADOS")
    print("="*50)
    print(df_territorios.head(10).to_string(index=False))
    print("="*50)