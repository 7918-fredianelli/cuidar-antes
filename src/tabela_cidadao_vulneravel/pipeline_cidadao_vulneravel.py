import os
import random
import re
import unicodedata
import pandas as pd
import numpy as np

# Importações locais dos ETLs da mesma pasta
try:
    from . import etl_idade_genero
    from . import etl_deficiencia
except ImportError:
    import etl_idade_genero
    import etl_deficiencia

def limpar_texto(texto):
    """Remove acentos, espaços extras e converte para minúsculas para cruzamento perfeito."""
    if pd.isna(texto):
        return ""
    nfkd = unicodedata.normalize('NFKD', str(texto))
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).strip().lower()

NOMES_FEMININOS = [
    "Ana", "Mariana", "Juliana", "Beatriz", "Larissa", "Fernanda", 
    "Camila", "Amanda", "Patrícia", "Vanessa", "Francisca", "Maria"
]

NOMES_MASCULINOS = [
    "Carlos", "José", "Lucas", "Gabriel", "Mateus", "Rafael", 
    "Bruno", "Thiago", "Rodrigo", "Diego", "Antônio", "João"
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
    "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
    "Soares", "Fernandes", "Vieira", "Barbosa", "D'Ávila", "D'El Rey", "Da Mota"
]

LOGRADOUROS_COMUNS = [
    "Rua das Flores", "Avenida Principal", "Rua do Sossego", "Travessa Santa Luzia",
    "Rua São João", "Avenida Beira Rio", "Rua Projetada A", "Beco do Riacho",
    "Rua Principal do Morro", "Avenida Marginal", "Ladeira da Paz", "Rua D'El Rey"
]

def gerar_nome(genero="M"):
    if genero == "F":
        primeiro = random.choice(NOMES_FEMININOS)
    else:
        primeiro = random.choice(NOMES_MASCULINOS)
    sobrenome1 = random.choice(SOBRENOMES)
    sobrenome2 = random.choice(SOBRENOMES)
    return f"{primeiro} {sobrenome1} {sobrenome2}"

def gerar_telefone_ficticio():
    """Gera telefone celular no padrão brasileiro atual com 9 dígitos: (DD) 9XXXX-XXXX"""
    ddd = random.choice(["31", "69", "11", "21", "85", "41", "61", "62", "43"])
    prefixo = random.randint(90000, 99999)
    sufixo = random.randint(1000, 9999)
    return f"({ddd}) {prefixo}-{sufixo}"

def executar_pipeline_cidadao(ids_filtrados=None):
    print("="*95)
    print("🚀 [Pipeline Cidadão Vulnerável] Executando com Prevenção de Conflito de Colunas")
    print("="*95)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_dir = os.path.join(base_dir, "../../sql")
    os.makedirs(sql_dir, exist_ok=True)
    
    # 1. Carrega as bases limpas pelos ETLs locais
    df_idade = etl_idade_genero.rodar_etl_idade_genero()
    df_def = etl_deficiencia.processar_deficiencia()
    
    # Padronização e criação segura das chaves canônicas em df_idade
    if not df_idade.empty:
        col_mun_idade = 'nome_cidade' if 'nome_cidade' in df_idade.columns else 'nome_municipio'
        df_idade['chave_mun'] = df_idade[col_mun_idade].apply(limpar_texto)
        df_idade['chave_uf'] = df_idade['uf'].apply(limpar_texto)
        
    # Padronização e criação segura das chaves canônicas em df_def
    if not df_def.empty:
        col_mun_def = 'nome_cidade' if 'nome_cidade' in df_def.columns else 'nome_municipio'
        df_def['chave_mun'] = df_def[col_mun_def].apply(limpar_texto)
        df_def['chave_uf'] = df_def['uf'].apply(limpar_texto)
    
    # 2. Lê o arquivo SQL de riscos gerado na Etapa 1 com parser robusto
    caminho_sql_risco = os.path.join(sql_dir, "insert_TB_TERRITORIO_SETOR_RISCO.sql")
    
    if not os.path.exists(caminho_sql_risco):
        print("❌ Erro: O arquivo de setores de risco não foi encontrado. Execute a etapa anterior primeiro.")
        return pd.DataFrame()
    
    setores_dados = []
    with open(caminho_sql_risco, 'r', encoding='utf-8') as f:
        for linha in f:
            if "INSERT INTO TB_TERRITORIO_SETOR_RISCO" in linha:
                try:
                    match_valores = re.search(r"VALUES \((.*?)\);", linha)
                    if not match_valores:
                        continue
                    
                    conteudo_valores = match_valores.group(1)
                    partes = [p.strip() for p in re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", conteudo_valores)]
                    
                    id_setor = int(partes[0])
                    nome_mun = partes[2].strip("'").replace("''", "'")
                    sigla_uf = partes[3].strip("'")
                    
                    setores_dados.append({
                        'id_setor': id_setor,
                        'nome_cidade': nome_mun,
                        'uf': sigla_uf,
                        'chave_mun': limpar_texto(nome_mun),
                        'chave_uf': limpar_texto(sigla_uf)
                    })
                except Exception:
                    continue
                
    df_setores = pd.DataFrame(setores_dados)
    if df_setores.empty:
        print("❌ Erro: Nenhum setor encontrado no arquivo SQL de riscos.")
        return pd.DataFrame()

    # Restringe estritamente para processar apenas um único ID por vez
    if ids_filtrados:
        primeiro_id = str(ids_filtrados[0]).strip()
        if primeiro_id.isdigit():
            df_setores = df_setores[df_setores['id_setor'] == int(primeiro_id)]

    if df_setores.empty:
        print("⚠️ Nenhum setor corresponde ao ID informado.")
        return pd.DataFrame()

    # 3. Cruzamento estrito selecionando apenas as colunas métricas de idade (evita colisão _x / _y)
    colunas_para_trazer_idade = ['chave_mun', 'chave_uf'] + [c for c in df_idade.columns if c not in ['nome_cidade', 'nome_municipio', 'uf', 'chave_mun', 'chave_uf']]
    df_merged = pd.merge(df_setores, df_idade[colunas_para_trazer_idade], on=['chave_mun', 'chave_uf'], how='inner')
    
    # Se o merge exato vier vazio, tenta flexibilizar apenas pela chave do município
    if df_merged.empty and not df_idade.empty:
        print("⚠️ [AVISO] Cruzamento exato por Município+UF retornou vazio. Tentando cruzamento flexível por Nome do Município...")
        colunas_flex_idade = ['chave_mun'] + [c for c in df_idade.columns if c not in ['nome_cidade', 'nome_municipio', 'uf', 'chave_mun', 'chave_uf']]
        df_merged = pd.merge(df_setores, df_idade[colunas_flex_idade].drop_duplicates(subset=['chave_mun']), on=['chave_mun'], how='inner')

    # Merge seguro para deficiência
    if not df_def.empty and 'total_deficientes' in df_def.columns:
        colunas_deficiencia = ['chave_mun', 'total_deficientes', 'total_mulheres'] if 'total_mulheres' in df_def.columns else ['chave_mun', 'total_deficientes']
        df_merged = pd.merge(df_merged, df_def[colunas_deficiencia].drop_duplicates(subset=['chave_mun']), on=['chave_mun'], how='left', suffixes=('', '_def'))
        df_merged['total_deficientes'] = df_merged['total_deficientes'].fillna(0).astype(int)
    else:
        df_merged['total_deficientes'] = 0

    # Tratamento seguro para contagem de mulheres
    if 'total_mulheres' in df_merged.columns:
        df_merged['total_mulheres'] = df_merged['total_mulheres'].fillna(0).astype(int)
    elif 'total_mulheres_def' in df_merged.columns:
        df_merged['total_mulheres'] = df_merged['total_mulheres_def'].fillna(0).astype(int)
    else:
        df_merged['total_mulheres'] = 50

    registros_cidadao = []
    id_cidadao_seq = 1
    auditoria_populacao = []

    print("\n🔄 Distribuindo vulnerabilidades de mobilidade de forma balanceada para o setor selecionado...")

    if df_merged.empty:
        print("⚠️ [AVISO] Merge indisponível. Ativando preenchimento automático de fallback estrutural...")
        df_alvo = df_setores.copy()
        modo_fallback = True
    else:
        df_alvo = df_merged
        modo_fallback = False

    for _, row in df_alvo.iterrows():
        id_setor = int(row['id_setor'])
        nome_mun = row['nome_cidade']
        uf = row['uf'] if 'uf' in row else 'SP'
        
        if modo_fallback:
            populacao_total = 350
            qtd_deficientes = 15
            idosos = 60
            acamados = 10
            gestantes = 10
        else:
            colunas_faixas = ['0 a 4 anos', '5 a 9 anos', '10 a 14 anos', '50 a 59 anos', '60 a 69 anos', '70 anos ou mais']
            populacao_total = int(sum([row[col] for col in colunas_faixas if col in row]))
            if populacao_total <= 0:
                populacao_total = 300
                
            qtd_deficientes = int(row.get('total_deficientes', 5))
            idosos = int(row.get('60 a 69 anos', 0)) + int(row.get('70 anos ou mais', 0))
            acamados = int(row.get('0 a 4 anos', 0))
            total_mulheres = int(row.get('total_mulheres', 50))
            gestantes = max(2, int(total_mulheres * 0.03))
        
        if qtd_deficientes > populacao_total:
            qtd_deficientes = populacao_total

        indices_cidadaos = list(range(populacao_total))
        random.shuffle(indices_cidadaos)

        atribuicoes = ['SEM_RESTRICAO'] * populacao_total
        
        idx_cadeirante = indices_cidadaos[:qtd_deficientes]
        restante = indices_cidadaos[qtd_deficientes:]
        for idx in idx_cadeirante: atribuicoes[idx] = 'CADEIRANTE'
            
        idx_idosos = restante[:min(idosos, len(restante))]
        restante = restante[min(idosos, len(restante)):]
        for idx in idx_idosos: atribuicoes[idx] = 'IDOSO_RESTRITO'
            
        idx_acamados = restante[:min(acamados, len(restante))]
        restante = restante[min(acamados, len(restante)):]
        for idx in idx_acamados: atribuicoes[idx] = 'ACAMADO'
            
        idx_gestantes = restante[:min(gestantes, len(restante))]
        restante = restante[min(gestantes, len(restante)):]
        for idx in idx_gestantes: atribuicoes[idx] = 'GESTANTE_ALTO_RISCO'

        for condicao in atribuicoes:
            genero = "F" if condicao == 'GESTANTE_ALTO_RISCO' else random.choice(["M", "F"])
            nome_completo = gerar_nome(genero).replace("'", "''")
            
            logradouro = f"{random.choice(LOGRADOUROS_COMUNS)}, {random.randint(1, 2500)}".replace("'", "''")
            telefone = gerar_telefone_ficticio()
            
            registros_cidadao.append({
                'id_cidadao': id_cidadao_seq,
                'id_setor': id_setor,
                'nome_completo': nome_completo,
                'logradouro_operacional': logradouro,
                'condicao_mobilidade': condicao,
                'telefone_contato': telefone
            })
            id_cidadao_seq += 1

        auditoria_populacao.append({
            'Município': nome_mun,
            'UF': uf,
            'Setor': id_setor,
            'População': populacao_total,
            'Cadeirante': atribuicoes.count('CADEIRANTE'),
            'Idoso': atribuicoes.count('IDOSO_RESTRITO'),
            'Acamado': atribuicoes.count('ACAMADO'),
            'Gestante': atribuicoes.count('GESTANTE_ALTO_RISCO'),
            'Sem Restrição': atribuicoes.count('SEM_RESTRICAO')
        })

    df_final = pd.DataFrame(registros_cidadao)

    # -------------------------------------------------------------
    # GARANTIA DE VOLUME MÍNIMO (>= 15.000 REGISTROS)
    # -------------------------------------------------------------
    META_MINIMA = 15000
    if len(df_final) < META_MINIMA and len(df_setores) > 0:
        deficit = META_MINIMA - len(df_final)
        print(f"\n⚠️ Volume atual ({len(df_final)}) abaixo da meta. Gerando lote complementar de {deficit} registros...")
        
        primeiro_setor = int(df_setores.iloc[0]['id_setor'])
        novos_registros = []
        
        for i in range(deficit):
            condicao = random.choice(['SEM_RESTRICAO', 'SEM_RESTRICAO', 'SEM_RESTRICAO', 'CADEIRANTE', 'IDOSO_RESTRITO', 'ACAMADO', 'GESTANTE_ALTO_RISCO'])
            genero = "F" if condicao == 'GESTANTE_ALTO_RISCO' else random.choice(["M", "F"])
            nome_completo = gerar_nome(genero).replace("'", "''")
            logradouro = f"{random.choice(LOGRADOUROS_COMUNS)}, {random.randint(1, 2500)}".replace("'", "''")
            telefone = gerar_telefone_ficticio()
            
            novos_registros.append({
                'id_cidadao': id_cidadao_seq + i,
                'id_setor': primeiro_setor,
                'nome_completo': nome_completo,
                'logradouro_operacional': logradouro,
                'condicao_mobilidade': condicao,
                'telefone_contato': telefone
            })
            
        df_final = pd.concat([df_final, pd.DataFrame(novos_registros)], ignore_index=True)

    df_final = df_final.sort_values(by=['id_setor', 'id_cidadao'], ascending=[True, True]).reset_index(drop=True)

    if auditoria_populacao:
        df_aud = pd.DataFrame(auditoria_populacao)
        print("\n" + "="*95)
        print("🔍 AUDITORIA DA DISTRIBUIÇÃO POR SETOR SELECIONADO")
        print("="*95)
        print(df_aud.to_string(index=False))
        print(f"... Total consolidado de cidadãos gerados: {len(df_final)}")
        print("="*95 + "\n")

    # 4. Geração do arquivo SQL de Cidadãos ordenado
    caminho_sql = os.path.join(sql_dir, "insert_TB_CIDADAO_VULNERAVEL.sql")

    print(f"💾 Escrevendo {len(df_final)} registros ordenados em {caminho_sql}...")
    
    with open(caminho_sql, 'w', encoding='utf-8') as f:
        f.write("-- Script SQL gerado automaticamente pelo Pipeline Cidadão (Compatível com Oracle SQL 11g/12c/19c)\n")
        f.write(f"-- Tabela: TB_CIDADAO_VULNERAVEL | Total de Registros: {len(df_final)} | Setor Processado Individualmente\n\n")
        
        for _, row in df_final.iterrows():
            colunas = list(row.index)
            valores = []
            for col in colunas:
                val = row[col]
                if pd.isna(val):
                    valores.append("NULL")
                elif col in ['id_cidadao', 'id_setor']:
                    valores.append(str(int(val)))
                else:
                    valores.append(f"'{str(val)}'")
            
            colunas_str = ", ".join(colunas)
            valores_str = ", ".join(valores)
            f.write(f"INSERT INTO TB_CIDADAO_VULNERAVEL ({colunas_str}) VALUES ({valores_str});\n")

    print(f"✅ Sucesso! Arquivo SQL gerado em: {caminho_sql} com {len(df_final)} registros.")
    return df_final

if __name__ == "__main__":
    executar_pipeline_cidadao()