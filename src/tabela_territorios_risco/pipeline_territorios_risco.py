import os
import unicodedata
import pandas as pd

# Importação local dos módulos ETL da mesma pasta
try:
    from . import etl_territorios
    from . import etl_alagamentos
    from . import etl_erosivos
    from . import etl_desabrigados
    from . import etl_obitos
    from . import etl_sem_internet
    from . import etl_dificil_acesso
except ImportError:
    import etl_territorios
    import etl_alagamentos
    import etl_erosivos
    import etl_desabrigados
    import etl_obitos
    import etl_sem_internet
    import etl_dificil_acesso

def limpar_texto(texto):
    """Remove acentos, espaços extras e converte para minúsculas para cruzamento perfeito."""
    if pd.isna(texto):
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).strip().lower()

def executar_etl_master(ufs_desejadas=None):
    print("="*90)
    print("🚀 [ETL Master - FIAP Compliance] Pipeline com Tipologia Completa de Desastres Naturais")
    print("="*90)
    
    if ufs_desejadas is None:
        ufs_desejadas = ["RO"]
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "../../output")
    sql_dir = os.path.join(base_dir, "../../sql")
    
    os.makedirs(sql_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Executa os módulos ETL
    try:
        df_territorios = etl_territorios.processar_territorios()
        df_alagamentos = etl_alagamentos.processar_alagamentos()
        df_erosivos = etl_erosivos.processar_erosivos()
        df_desabrigados = etl_desabrigados.rodar_etl_desabrigados()
        df_obitos = etl_obitos.rodar_etl_obitos()
        df_sem_internet = etl_sem_internet.processar_sem_internet()
        df_dificil_acesso = etl_dificil_acesso.processar_dificil_acesso()
    except Exception as e:
        print(f"❌ Erro na execução dos ETLs: {e}")
        return pd.DataFrame()

    if df_territorios.empty:
        print("❌ Erro: A base de territórios está vazia.")
        return pd.DataFrame()

    # 2. Prepara a base mestre (Territórios)
    df_base = df_territorios.copy()
    df_base['nome_cidade'] = df_base['nome_cidade'].astype(str).str.strip().str.title()
    df_base['uf'] = df_base['uf'].astype(str).str.strip().str.upper()
    df_base['cd_ibge_municipio'] = pd.to_numeric(df_base['codigo_cidade'], errors='coerce')

    # Filtra pelas UFs fornecidas pelo usuário
    df_filtrado = df_base[df_base['uf'].isin(ufs_desejadas)].copy()

    # Cria chaves canônicas de cruzamento
    df_filtrado['chave_mun'] = df_filtrado['nome_cidade'].apply(limpar_texto)
    df_filtrado['chave_uf'] = df_filtrado['uf'].apply(limpar_texto)
    df_filtrado = df_filtrado.drop_duplicates(subset=['chave_mun', 'chave_uf'])

    # 3. Função padrão de merge
    def aplicar_merge(df_principal, df_aux, col_metrica):
        if df_aux.empty:
            df_principal[col_metrica] = 0
            return df_principal
            
        temp = df_aux.copy()
        temp['chave_mun'] = temp['nome_cidade'].apply(limpar_texto)
        temp['chave_uf'] = temp['uf'].apply(limpar_texto)
        
        temp[col_metrica] = pd.to_numeric(temp[col_metrica], errors='coerce').fillna(0)
        temp_agg = temp.groupby(['chave_mun', 'chave_uf'], as_index=False)[col_metrica].sum()
        
        merged = pd.merge(df_principal, temp_agg[['chave_mun', 'chave_uf', col_metrica]], on=['chave_mun', 'chave_uf'], how='left')
        merged[col_metrica] = merged[col_metrica].fillna(0)
        return merged

    # 4. Aplica o cruzamento em cadeia
    df_merged = df_filtrado.copy()
    df_merged = aplicar_merge(df_merged, df_alagamentos, 'total_alagamentos')
    df_merged = aplicar_merge(df_merged, df_erosivos, 'total_processos_erosivos')
    df_merged = aplicar_merge(df_merged, df_desabrigados, 'total_desabrigados')
    df_merged = aplicar_merge(df_merged, df_obitos, 'total_obitos')
    df_merged = aplicar_merge(df_merged, df_sem_internet, 'total_sem_internet')
    df_merged = aplicar_merge(df_merged, df_dificil_acesso, 'total_geral_pessoas')

    registros_gerados = 0
    dados_consolidados = []
    id_setor_seq = 1
    auditoria_dados = []

    # 5. Aplicação da Regra de Pontuação e Risco
    for _, row in df_merged.iterrows():
        cd_ibge = row['cd_ibge_municipio']
        nome_mun = row['nome_cidade']
        sigla_uf = row['uf']
        
        alag = row['total_alagamentos']
        eros = row['total_processos_erosivos']
        desab = row['total_desabrigados']
        obitos = row['total_obitos']
        net = row['total_sem_internet']
        dacesso = row['total_geral_pessoas']

        if pd.isna(nome_mun) or pd.isna(cd_ibge):
            continue

        score = 0
        if alag == 1: score += 1
        elif alag > 1: score += 2

        if desab == 1: score += 5
        elif desab > 1: score += 7

        if eros == 1: score += 1
        elif eros > 1: score += 2

        if obitos == 1: score += 5
        elif obitos > 1: score += 7

        pontos_outras_ameacas = score

        if net > 0 and pontos_outras_ameacas > 0:
            score += 2

        if dacesso > 10 and pontos_outras_ameacas > 0:
            score += 4

        if score > 15:
            grau_risco, status_setor = 'MUITO_ALTO', 'ALERTA_EVACUACAO'
        elif 10 <= score <= 15:
            grau_risco, status_setor = 'ALTO', 'INTERDITADO'
        elif 5 <= score <= 9:
            grau_risco, status_setor = 'MEDIO', 'ATENCAO'
        else:
            grau_risco, status_setor = 'BAIXO', 'NORMAL'

        if alag > eros and alag > 0:
            tipo_ameaca = 'INUNDACAO'
            cota_topografica = 12.00
        elif eros >= alag and eros > 0:
            tipo_ameaca = 'ENXURRADA'
            cota_topografica = 45.00
        else:
            if id_setor_seq % 3 == 0:
                tipo_ameaca = 'INUNDACAO'
                cota_topografica = 12.00
            elif id_setor_seq % 3 == 1:
                tipo_ameaca = 'ENXURRADA'
                cota_topografica = 45.00
            else:
                tipo_ameaca = 'DESLIZAMENTO'
                cota_topografica = 150.00

        auditoria_dados.append({
            'Município': nome_mun,
            'Alag': alag,
            'Eros': eros,
            'Score': score,
            'Risco': grau_risco,
            'Status': status_setor,
            'Ameaça': tipo_ameaca,
            'Cota': cota_topografica
        })

        nome_sanitizado = nome_mun.replace("'", "''")
        nome_comunidade = f"Área Vulnerável ({tipo_ameaca}) - {nome_sanitizado}"

        dados_consolidados.append({
            'id_setor': id_setor_seq,
            'cd_ibge_municipio': int(cd_ibge),
            'nome_municipio': nome_sanitizado,
            'uf': sigla_uf,
            'nome_comunidade': nome_comunidade,
            'grau_risco': grau_risco,
            'tipo_ameaca': tipo_ameaca,
            'cota_topografica': cota_topografica,
            'status_setor': status_setor
        })
        id_setor_seq += 1
        registros_gerados += 1

    df_aud = pd.DataFrame(auditoria_dados)
    print("\n" + "="*85)
    print("🔍 RELATÓRIO DE AUDITORIA DO CÁLCULO E TIPOLOGIAS (AMOSTRA)")
    print("="*85)
    print(df_aud.head(15).to_string(index=False))
    print("="*85 + "\n")

    # 6. Geração do SQL
    df_final = pd.DataFrame(dados_consolidados)
    caminho_sql = os.path.join(sql_dir, "insert_TB_TERRITORIO_SETOR_RISCO.sql")

    ufs_str_label = ", ".join(ufs_desejadas)
    with open(caminho_sql, 'w', encoding='utf-8') as f:
        f.write("-- Script SQL gerado automaticamente pelo ETL Master (Compatível com Oracle SQL 11g/12c/19c)\n")
        f.write(f"-- Tabela: TB_TERRITORIO_SETOR_RISCO | UF(s): {ufs_str_label} | Total: {len(df_final)} registros\n\n")
        
        for _, row in df_final.iterrows():
            colunas = list(row.index)
            valores = []
            for col in colunas:
                val = row[col]
                if pd.isna(val):
                    valores.append("NULL")
                elif col in ['id_setor', 'cd_ibge_municipio']:
                    valores.append(str(int(val)))
                elif col == 'cota_topografica':
                    valores.append(f"{float(val):.2f}")
                else:
                    valores.append(f"'{str(val)}'")
            
            colunas_str = ", ".join(colunas)
            valores_str = ", ".join(valores)
            f.write(f"INSERT INTO TB_TERRITORIO_SETOR_RISCO ({colunas_str}) VALUES ({valores_str});\n")

    print(f"✅ Pipeline concluído com sucesso! {registros_gerados} registros gravados em {caminho_sql}")
    return df_final

if __name__ == "__main__":
    executar_etl_master(["RO"])