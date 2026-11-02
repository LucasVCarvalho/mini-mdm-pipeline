# Mini MDM Pipeline

Projeto de estudo que simula um problema real de **Master Data Management (MDM)**: o mesmo cliente cadastrado em vários sistemas, com dados inconsistentes, que precisa virar um registro único e confiável (*golden record*).

> **Status:** em andamento. Veja o [roadmap](#roadmap).

## O problema

Um banco fictício tem três sistemas que não compartilham identificadores: **conta corrente**, **cartões** e **seguros**. Cada um guarda os clientes do seu jeito, e o objetivo do pipeline é descobrir quais registros representam a mesma pessoa, sem acesso a nenhum identificador comum.

## Stack

- **Python 3** com Faker para geração de dados sintéticos
- **Apache Airflow** em Docker para orquestração
- **PostgreSQL 16** como banco de dados do projeto, separado do banco de metadados do Airflow
- Ambiente: Docker Desktop + WSL2 (Ubuntu)

## Estrutura

```
mini-mdm-pipeline/
├── dags/                   # DAGs do Airflow
├── scripts/
│   ├── gerar_dados.py      # gerador de dados sintéticos
│   └── match_teste.py      # match experimental + avaliação
├── sql/                    # consultas do pipeline
├── data/                   # gerado pelos scripts (fora do Git)
│   ├── fontes/             # o que o pipeline lê
│   └── gabarito/           # usado só na avaliação
└── docker-compose.yaml
```

## Como rodar

```bash
# 1. Variáveis de ambiente
echo -e "AIRFLOW_UID=$(id -u)" > .env
echo "FERNET_KEY=$(openssl rand -base64 32 | tr '+/' '-_')" >> .env

# 2. Subir o ambiente (Airflow em http://localhost:8080)
docker compose up airflow-init
docker compose up -d

# 3. Gerar os dados e rodar o teste de match
python3 -m venv .venv && source .venv/bin/activate
pip install faker
python scripts/gerar_dados.py
python scripts/match_teste.py
```

## Dados sintéticos

O gerador cria 1.000 pessoas e as distribui entre os sistemas (90% em conta corrente, 60% em cartões, 40% em seguros). Cada sistema introduz problemas comuns em cadastros reais:

| Sistema | Problemas simulados |
|---|---|
| Conta corrente | Referência: CPF com máscara, dados completos |
| Cartões | Nome em maiúsculas e sem acento, CPF só com números, CPF ausente em 10% |
| Seguros | Nome do meio abreviado, data em DD/MM/AAAA, CPF ausente ou com dígito verificador inválido, endereço desatualizado |
| Todos | E-mails com maiúsculas ou espaços; e-mail alternativo em vez do principal |

A **seed é fixa**, então qualquer pessoa que rodar o gerador obtém exatamente os mesmos dados.

## Avaliação do match

Como o gerador sabe quem é quem, ele grava um **gabarito** numa pasta separada. O pipeline **nunca lê esse arquivo**: usar a resposta durante o processamento seria vazamento de dados (*data leakage*). O gabarito serve apenas para medir:

- **Precisão:** dos matches feitos, quantos estavam certos (mede junções erradas de pessoas diferentes)
- **Recall:** dos pares reais, quantos foram encontrados (mede duplicados não detectados)

### Resultados até agora (match por e-mail + data de nascimento normalizados)

| Cenário | Precisão | Recall |
|---|---|---|
| Dados iniciais | 100% (249/249) | 100% (249/249) |
| Com e-mails alternativos | 100% (170/170) | 68% (170/249) |

O primeiro resultado perfeito indicava que os dados de teste eram fáceis demais, e não que o match era bom. Com e-mails alternativos, o recall caiu para 68%, próximo dos ~67,5% previstos pelas probabilidades do gerador. A conclusão é que um único critério de match não é suficiente, o que motiva o match por pontuação.

## Decisões de design

- **Banco do projeto separado do banco de metadados do Airflow**, para não misturar responsabilidades.
- **Versões de imagem fixadas** (`postgres:16`) para um ambiente reproduzível.
- **Segredos fora do Git**: a Fernet key fica no `.env`, que está no `.gitignore`.
- **Padronização antes da comparação**: e-mails e datas são normalizados uma única vez.
- **Índice em dicionário em vez de loop aninhado**: cada registro é consultado pela chave de match, evitando comparar todos com todos (mesma ideia do *blocking*).
- **Partes do nome guardadas separadamente na geração**: separar um nome completo depois não é confiável por causa de nomes compostos e partículas ("da", "dos").

## Roadmap

- [x] Ambiente Airflow + PostgreSQL em Docker
- [x] Gerador de dados sintéticos com gabarito
- [x] Match experimental com medição de precisão e recall
- [ ] Mais cenários: e-mail ausente, dia e mês trocados, gêmeos que compartilham e-mail
- [ ] DAG de ingestão com camada bruta e quarentena de registros inválidos
- [ ] Validação de CPF pelo dígito verificador
- [ ] Match por pontuação combinando CPF, similaridade de nome, data e e-mail
- [ ] Golden record com regras de sobrevivência e tabela de referência cruzada
- [ ] Dimensão de clientes em SCD Tipo 2
- [ ] Pipeline idempotente
- [ ] Match em PySpark

## Autor

Lucas Viana Carvalho
