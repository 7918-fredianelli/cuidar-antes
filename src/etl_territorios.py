import os
import pandas as pd

# Dicionário oficial de conversão do Código numérico da UF para a Sigla
MAP_CODIGO_UF = {
    11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
    21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL',
    28: 'SE', 29: 'BA', 31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR',
    42: 'SC', 43: 'RS', 50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
}

def converte_uf_sigla(val):
    try:
        num = int(float(val))
        return MAP_CODIGO_UF.get(num, "").upper()
    except (ValueError, TypeError):
        return str(val).strip().upper()

def processar_territorios():
    """
    Processa a base de territórios (Fonte da Verdade) padronizando os campos essenciais:
    [codigo_uf, nome_uf, codigo_cidade, nome_cidade, uf, abreviacao_cidade]
    """
    print("[ETL Territórios] Iniciando processamento da base de territórios...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(base_dir, "../data/territorios.csv")
    
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
        
    # Inicia a leitura a partir da linha 7 (skiprows=6)
    df = pd.read_csv(caminho_arquivo, header=None, skiprows=6, sep=';', encoding='utf-8-sig', low_memory=False, dtype=str)
    
    # Renomeia as colunas dinamicamente
    df.columns = [f"col_{i}" for i in range(len(df.columns))]
    
    df_final = pd.DataFrame()
    df_final['codigo_uf'] = df['col_0'].str.strip()
    df_final['nome_uf'] = df['col_1'].str.strip()
    df_final['codigo_cidade'] = df['col_7'].str.strip()
    df_final['nome_cidade'] = df['col_8'].str.strip().str.title()
    
    # Deriva a sigla da UF a partir do código numérico para unificação de contratos
    df_final['uf'] = df_final['codigo_uf'].apply(converte_uf_sigla)
    
    # Cria a abreviação padrão baseada nas iniciais
    df_final['abreviacao_cidade'] = df_final['nome_cidade'].apply(
        lambda x: ''.join([w[0] for w in x.split()]).upper() if isinstance(x, str) else ''
    )
    
    # Remove linhas vazias ou nulas essenciais
    df_final = df_final.dropna(subset=['codigo_cidade', 'nome_cidade', 'uf'])
    
    print(f"[ETL Territórios] Sucesso! {len(df_final)} registros processados.")
    return df_final

if __name__ == "__main__":
    df_territorios = processar_territorios()
    
    print("\n" + "="*50)
    print("🔍 TESTE VISUAL: TERRITÓRIOS PROCESSADOS")
    print("="*50)
    print(df_territorios.head(10).to_string(index=False))
    print("="*50)