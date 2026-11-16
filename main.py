import os
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
    
    # Fallback automático se o usuário apenas apertar ENTER
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
    
    # Lê os setores gerados no Passo 1 para exibir na tela
    caminho_sql_risco = os.path.join(sql_dir, "insert_TB_TERRITORIO_SETOR_RISCO.sql")
    setores_disponiveis = []
    
    if os.path.exists(caminho_sql_risco):
        with open(caminho_sql_risco, 'r', encoding='utf-8') as f:
            for linha in f:
                if "INSERT INTO TB_TERRITORIO_SETOR_RISCO" in linha:
                    try:
                        partes = linha.split("VALUES (")[1].rstrip(");\n").split(", ")
                        id_s = partes[0]
                        mun = partes[2].strip("'").replace("''", "'")
                        uf_s = partes[3].strip("'")
                        setores_disponiveis.append((id_s, mun, uf_s))
                    except Exception:
                        continue

    # Exibe até 3 sugestões de IDs e cidades disponíveis para guiar o usuário
    if setores_disponiveis:
        print("\n💡 Sugestões de Setores Disponíveis:")
        for id_s, mun, uf_s in setores_disponiveis[:3]:
            print(f"   • ID Setor: {id_s} -> {mun} ({uf_s})")
        if len(setores_disponiveis) > 3:
            print(f"   ... e mais {len(setores_disponiveis) - 3} setor(es) gerado(s).")
        print()

    entrada_ids = input("👉 Digite o ID do Setor [ou ENTER para distribuir em todos]: ").strip()
    
    # Fallback: Se der ENTER, distribui automaticamente em todos os setores gerados
    if not entrada_ids:
        ids_filtrados = [s[0] for s in setores_disponiveis]
        print("   -> ENTER pressionado: Distribuindo cidadãos em todos os setores gerados.")
    else:
        ids_filtrados = [i.strip() for i in entrada_ids.split(",")]
        print(f"   -> Setor(es) selecionado(s) para processamento: {ids_filtrados}")
        
    try:
        print("\n🎲 Gerando cidadãos sintéticos vinculados aos setores...")
        executar_cidadao(ids_filtrados)
        print(f"✅ Arquivos SQL gerados com sucesso na pasta 'sql/'!")
    except Exception as e:
        print(f"❌ Erro ao gerar os cidadãos vulneráveis: {e}")

    print("="*65)

if __name__ == "__main__":
    executar_orquestrador()