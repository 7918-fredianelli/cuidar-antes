import os
import pandas as pd

def processar_dificil_acesso():
    """
    Processa a base de difícil acesso seguindo o contrato padrão de saída:
    [nome_cidade, uf, total_geral_pessoas]
    """
    print("[ETL Difícil Acesso] Iniciando processamento da base...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(base_dir, "../../data/territorios/dificil_acesso_.csv")
    
    if not os.path.exists(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    df = pd.read_csv(
        caminho_arquivo,
        sep=";",
        skiprows=6,
        header=None,
        encoding="utf-8",
        dtype=str
    )
    
    df = df[[0, 1, 5, 6]].copy()
    df.columns = ["municipio_raw", "caracteristica", "soma", "total_geral"]
    df = df.dropna(subset=["caracteristica"])
    df["municipio_raw"] = df["municipio_raw"].ffill()
    
    extracao = df["municipio_raw"].str.extract(r"^(.*?)\s*\(([A-Z]{2})\)$")
    df["nome_cidade"] = extracao[0].str.strip().str.title()
    df["uf"] = extracao[1].str.strip().str.upper()

    df["total_geral"] = pd.to_numeric(df["total_geral"].str.replace(',', '.', regex=False), errors="coerce").fillna(0)

    # Extrai o total geral de pessoas por município/UF
    df_final = (
        df.dropna(subset=["nome_cidade", "uf", "total_geral"])
        .groupby(["nome_cidade", "uf"], as_index=False)["total_geral"]
        .first()
    )
    
    df_final["total_geral_pessoas"] = df_final["total_geral"].astype(int)
    df_final = df_final[["nome_cidade", "uf", "total_geral_pessoas"]]

    print(f"[ETL Difícil Acesso] Sucesso! {len(df_final)} municípios processados.")
    return df_final

if __name__ == "__main__":
    df_resultado = processar_dificil_acesso()
    print("\n" + "="*50)
    print("🔍 TESTE VISUAL: DIFÍCIL ACESSO")
    print("="*50)
    print(df_resultado.head(10).to_string(index=False))
    print("="*50)