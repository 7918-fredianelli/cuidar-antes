import os
import re
import sys
import pandas as pd

# Adiciona a raiz do projeto ao path do Python
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)

# Importações dos pipelines respeitando a árvore de pastas
try:
    from src.tabela_territorios_risco.pipeline_territorios_risco import executar_etl_master as executar_risco
    from src.tabela_cidadao_vulneravel.pipeline_cidadao_vulneravel import executar_pipeline_cidadao as executar_cidadao
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("💡 Verifique se as pastas possuem o arquivo '__init__.py'.")
    sys.exit(1)

def executar_orquestrador():
    print("="*65)
    print(" 🛡️ CUIDAR ANTES - PLATAFORMA DE ORQUESTRAÇÃO DE CARGA (ETL/SQL)")
    print("="*65)
    
    sql_dir = os.path.join(base_dir, "sql")
    os.makedirs(sql_dir, exist_ok=True)
    
    # -------------------------------------------------------------
    # PASSO 1/2: Carga de Territórios de Risco (IBGE)
    # -------------------------------------------------------------
    print("\n[Passo 1/2] Carga de Territórios de Risco (IBGE)")
    entrada_ufs = input("👉 Digite as UFs desejadas (ex: SP,RJ) [Padrão: SP]: ").strip()
    
    if not entrada_ufs:
        ufs_desejadas = ["SP"]
        print("   -> Nenhuma UF informada. Aplicando padrão: SP")
    else:
        ufs_desejadas = [uf.strip().upper() for uf in entrada_ufs.split(",")]
    
    print(f"\n⏳ Processando base IBGE para {', '.join(ufs_desejadas)}...")
    
    try:
        df_risco = executar_risco(ufs_desejadas)
        if df_risco is None or df_risco.empty:
            print("❌ O processamento de riscos retornou uma base vazia. Verifique os arquivos CSV.")
            return
        total_setores = len(df_risco)
        print(f"✅ {total_setores} Setores de Risco gerados com sucesso (IDs de 1 a {total_setores}).")
    except Exception as e:
        print(f"❌ Erro ao executar o pipeline de setores de risco: {e}")
        return

    # -------------------------------------------------------------
    # PASSO 2/2: Carga de Cidadãos Vulneráveis (Pessoas Protegidas)
    # -------------------------------------------------------------
    print("\n" + "-"*65)
    print("[Passo 2/2] Carga de Cidadãos Vulneráveis (Pessoas Protegidas)")
    
    # Lê os setores gerados no Passo 1 com parser regex robusto
    caminho_sql_risco = os.path.join(sql_dir, "insert_TB_TERRITORIO_SETOR_RISCO.sql")
    setores_disponiveis = []
    
    if os.path.exists(caminho_sql_risco):
        with open(caminho_sql_risco, 'r', encoding='utf-8') as f:
            for linha in f:
                if "INSERT INTO TB_TERRITORIO_SETOR_RISCO" in linha:
                    try:
                        match_valores = re.search(r"VALUES \((.*?)\);", linha)
                        if not match_valores:
                            continue
                        conteudo_valores = match_valores.group(1)
                        partes = [p.strip() for p in re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", conteudo_valores)]
                        
                        id_s = partes[0]
                        mun = partes[2].strip("'").replace("''", "'")
                        uf_s = partes[3].strip("'")
                        setores_disponiveis.append((id_s, mun, uf_s))
                    except Exception:
                        continue

    # Exibe sugestões de setores disponíveis para guiar o usuário
    if setores_disponiveis:
        print("\n💡 Sugestões de Setores Disponíveis:")
        for id_s, mun, uf_s in setores_disponiveis[:3]:
            print(f"   • ID Setor: {id_s} -> {mun} ({uf_s})")
        if len(setores_disponiveis) > 3:
            print(f"   ... e mais {len(setores_disponiveis) - 3} setor(es) gerado(s).")
        print()

    entrada_id = input("👉 Digite um ÚNICO ID de Setor por vez (ex: 535) [ou ENTER para pegar o primeiro]: ").strip()
    
    # Se der ENTER ou valor inválido, assume o primeiro ID disponível
    if not entrada_id or not entrada_id.isdigit():
        if setores_disponiveis:
            ids_filtrados = [setores_disponiveis[0][0]]
            print(f"   -> Nenhum ID válido informado. Utilizando o primeiro setor disponível (ID: {ids_filtrados[0]}).")
        else:
            ids_filtrados = ["1"]
    else:
        ids_filtrados = [entrada_id]
        print(f"   -> Setor selecionado para processamento: ID {entrada_id}")
        
    try:
        print("\n🎲 Gerando cidadãos sintéticos vinculados ao setor selecionado...")
        executar_cidadao(ids_filtrados)
        print(f"✅ Arquivos SQL gerados com sucesso na pasta 'sql/'!")
    except Exception as e:
        print(f"❌ Erro ao gerar os cidadãos vulneráveis: {e}")

    print("="*65)

if __name__ == "__main__":
    executar_orquestrador()