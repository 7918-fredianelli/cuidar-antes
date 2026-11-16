Markdown
# 🛡️ Cuidar Antes - Sistema Integrado de Gestão de Desastres e Vulnerabilidade

Plataforma analítica e pipeline de ETL modular desenvolvido para o desafio da **FIAP**, com foco na prevenção de desastres naturais e na proteção proativa de populações vulneráveis em municípios brasileiros. O projeto integra dados demográficos e geoespaciais para gerar cargas SQL prontas para homologação e inserção em SGBDs relacionais corporativos (Compatível com **Oracle SQL 11g/12c/19c**).

---

## 🏗️ Arquitetura do Projeto

O projeto segue uma arquitetura orientada a domínios e separação de responsabilidades (Domain-Driven Design), gerenciada por um orquestrador central na raiz (`main.py`):

```text
Cuidar Antes/
│
├── main.py                          # Orquestrador Master (CLI)
├── README.md                        # Documentação do Projeto
├── requirements.txt                 # Dependências do Python
│
├── sql/                             # Scripts SQL gerados para o banco
│   ├── insert_TB_TERRITORIO_SETOR_RISCO.sql
│   └── insert_TB_CIDADAO_VULNERAVEL.sql
│
└── src/
    ├── __init__.py
    │
    ├── tabela_territorios_risco/    # Domínio 1: Mapeamento de Riscos e Setores
    │   ├── __init__.py
    │   ├── pipeline_territorios_risco.py
    │   ├── etl_territorios.py
    │   ├── etl_alagamentos.py
    │   ├── etl_erosivos.py
    │   ├── etl_desabrigados.py
    │   ├── etl_obitos.py
    │   ├── etl_sem_internet.py
    │   └── etl_dificil_acesso.py
    │
    └── tabela_cidadao_vulneravel/   # Domínio 2: Mapeamento de Cidadãos Protegidos
        ├── __init__.py
        ├── pipeline_cidadao_vulneravel.py
        ├── etl_idade_genero.py
        └── etl_deficiencia.py
⚙️ Regras de Negócio e Engenharia de Dados
Classificação de Riscos (TB_TERRITORIO_SETOR_RISCO):

Cruzamento automatizado de tipologias de desastres (alagamentos, processos erosivos, desabrigados, óbitos, isolamento digital e setores de difícil acesso).

Atribuição dinâmica de pontuação de risco (BAIXO, MÉDIO, ALTO, MUITO_ALTO) e definição de status operacionais (NORMAL, ATENÇÃO, INTERDITADO, ALERTA_EVACUACAO).

Distribuição de Vulnerabilidade e Cidadãos (TB_CIDADAO_VULNERAVEL):

Mapeamento estrito baseado em faixas etárias do IBGE (idosos, crianças/acamados) e dados de deficiência.

Regra de Conformidade para Gestantes: O status GESTANTE_ALTO_RISCO exige obrigatoriamente a atribuição de nomes femininos.

Mascara Telefônica Moderna: Geração de telefones celulares no padrão brasileiro com 9 dígitos (DD) 9XXXX-XXXX.

Blindagem e Meta Mínima: Sistema inteligente com fallback e preenchimento automático para garantir a entrega de no mínimo 15.000 registros de cidadãos por execução.

Ordenação: Scripts SQL gerados com ordenação numérica estrita e crescente por id_setor.

Compatibilidade Oracle SQL:

Sanitização robusta de strings aplicando .replace("'", "''") em logradouros, nomes e descrições para evitar erros de sintaxe (ORA-01756).

🚀 Como Executar o Projeto
1. Pré-requisitos
Certifique-se de ter o Python 3.8+ instalado em sua máquina.

2. Instalação de Dependências
Clone o repositório, ative o seu ambiente virtual (se houver) e instale as bibliotecas necessárias:

Bash
pip install -r requirements.txt
3. Execução do Orquestrador Master
Execute o script principal na raiz do projeto:

Bash
python main.py
O terminal interativo guiará você por 2 passos simples:

Passo 1: Informe a(s) sigla(s) da(s) UF(s) desejada(s) (Ex: RO, SP, AM) ou pressione ENTER para assumir o padrão.

Passo 2: Visualize sugestões de setores disponíveis e escolha um ID específico ou pressione ENTER para distribuir os cidadãos automaticamente em todos os setores gerados.

Os scripts SQL prontos para carga serão salvos automaticamente na pasta /sql.
