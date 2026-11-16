import pandas as pd

# 1. Carrega e processa a base completa
df = pd.read_csv(
    "data/dificil_acesso_.csv",
    sep=";",
    skiprows=6,
    header=None,
    encoding="utf-8",
)
df = df[[0, 1, 5, 6]].copy()
df.columns = ["municipio_raw", "caracteristica", "soma", "total_geral"]
df = df.dropna(subset=["caracteristica"])
df["municipio_raw"] = df["municipio_raw"].ffill()
df[["Cidade", "UF"]] = df["municipio_raw"].str.extract(
    r"^(.*?)\s*\(([A-Z]{2})\)$"
)

mapa_colunas = {
    "Capacidade máxima de circulação da via - Motocicletas, bicicletas e pedestres": (
        "Capacidade Max Motos e Pedestres"
    ),
    "Capacidade de circulação da via - Aquavias": "Total Aquavias",
    "Via pavimentada - Não existe": "Total Sem Pavimento",
    "Existência de iluminação pública - Não existe": (
        "Total Sem Iluminação Pública"
    ),
}
df["caracteristica"] = df["caracteristica"].replace(mapa_colunas)

df["soma"] = pd.to_numeric(df["soma"], errors="coerce").fillna(0).astype(int)
df["total_geral"] = pd.to_numeric(df["total_geral"], errors="coerce")

df_total = (
    df.dropna(subset=["total_geral"])
    .groupby(["Cidade", "UF"], as_index=False)["total_geral"]
    .first()
)
df_total["total_geral"] = df_total["total_geral"].astype(int)
df_total = df_total.rename(columns={"total_geral": "Total Geral Pessoas"})

df_pivot = df.pivot_table(
    index=["Cidade", "UF"],
    columns="caracteristica",
    values="soma",
    aggfunc="sum",
    fill_value=0,
).reset_index()

df_final = pd.merge(df_pivot, df_total, on=["Cidade", "UF"])
colunas_ordenadas = [
    "Cidade",
    "UF",
    "Capacidade Max Motos e Pedestres",
    "Total Aquavias",
    "Total Sem Pavimento",
    "Total Sem Iluminação Pública",
    "Total Geral Pessoas",
]
df_final = df_final[colunas_ordenadas]

# 2. Filtra apenas as 10 primeiras cidades
df_10 = df_final.head(10)

# 3. Exibe no terminal em formato de tabela
print(df_10.to_string(index=False))

# 4. Salva o recorte das 10 primeiras se desejar
df_10.to_csv(
    "data/dificil_acesso_primeiras_10.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig",
)