import csv
import random
import unicodedata
import re
from pathlib import Path

from faker import Faker

SEED = 42
N_PESSOAS = 1000

random.seed(SEED)
Faker.seed(SEED)
fake = Faker("pt_BR")
PASTA_SAIDA = Path(__file__).resolve().parent.parent / "data" / "fontes"
PASTA_GABARITO = Path(__file__).resolve().parent.parent / "data" / "gabarito"
PREPOSICOES = {"da", "das", "de", "do", "dos", "e"}

def gerar_pessoas(n):
    """Cria as pessoas 'reais', com dados limpos."""
    pessoas = []
    for i in range(1, n + 1):
        primeiro = fake.first_name()
        meio = fake.last_name()
        ultimo = fake.last_name()
        pessoas.append({
            "id_pessoa": i,
            "nome": f"{primeiro} {meio} {ultimo}",
            "primeiro_nome": primeiro,
            "nome_meio": meio,
            "ultimo_nome": ultimo,
            "cpf": fake.cpf(),
            "data_nascimento": fake.date_of_birth(minimum_age=18, maximum_age=85),
            "email": fake.email(),
            "email_alternativo": fake.free_email(),
            "telefone": fake.phone_number(),
            "endereco": fake.street_address(),
            "endereco_antigo": fake.street_address(),
        })
    return pessoas


# ---------- Funções  ----------

def remover_acentos(nome):
    # José Viana Magalhães -> Jose Viana Magalhaes
    # Aplica NFKD para separar os acentos das letras
    nfkd = unicodedata.normalize("NFKD", nome)
    
    # Filtra apenas os caracteres que não são combinantes (não são acentos)
    nome_sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])

    # Transforma tudo em upper case
    return nome_sem_acento

def abreviar_nome_do_meio(pessoa):
    # "Maria Souza Oliveira" -> "Maria S. Oliveira"
    # Transformando o nome em um array
    palavras = [p for p in pessoa["nome_meio"].split() if p.lower() not in PREPOSICOES]
    inicial = f"{palavras[0][0].upper()}."
    return f"{pessoa['primeiro_nome']} {inicial} {pessoa['ultimo_nome']}"


def invalidar_cpf(cpf):
    # Altere o último dígito para o CPF ficar inválido
    ultimo = int(cpf[-1])
    novo_ultimo = str((ultimo + 1) % 10)
    return cpf[:-1] + novo_ultimo

def apenas_numeros_cpf(cpf):
    # Tirar pontos do CPF e deixar apenas os numeros: 123.456.789-01 -> 12345678901
    cpf_limpo = re.sub(r"\D", "", cpf)
    return cpf_limpo

def sujar_email(email):
    # Maiúsculas ou espaços nas pontas
    if(random.random() <= 0.50):
        return " " + email + " "
    return email.upper()

def talvez_sujar_email(email):
    if random.random() < 0.10:
        return sujar_email(email)
    return email


# ---------- Montagem dos sistemas ----------

def montar_conta_corrente(pessoa, seq):
    return {
        "id_cliente": f"CC-{seq:05d}",
        "nome": pessoa["nome"],
        "cpf": pessoa["cpf"],
        "data_nascimento": pessoa["data_nascimento"].isoformat(),
        "email": talvez_sujar_email(pessoa["email"]),
        "telefone": pessoa["telefone"],
        "endereco": pessoa["endereco"],
    }


def montar_cartoes(pessoa, seq):
    sorteio = random.random()
    cpf = apenas_numeros_cpf(pessoa["cpf"])
    if sorteio < 0.10:
        cpf = ""

    return {
        "id_cliente": f"CT-{seq:05d}",
        "nome": remover_acentos(pessoa["nome"]).upper(),
        "cpf": cpf,
        "data_nascimento": pessoa["data_nascimento"].isoformat(),
        "email": talvez_sujar_email(pessoa["email"]) if sorteio < 0.20 else talvez_sujar_email(pessoa["email_alternativo"]),
        "telefone": pessoa["telefone"],
        "endereco": pessoa["endereco"],
    }


def montar_seguros(pessoa, seq):
    # Um único sorteio para dois casos que não podem acontecer juntos:
    # de 0 a 0.15 o CPF some; de 0.15 a 0.17 ele fica inválido
    sorteio = random.random()
    if sorteio < 0.15:
        cpf = ""
    elif sorteio < 0.17:
        cpf = invalidar_cpf(pessoa["cpf"])
    else:
        cpf = pessoa["cpf"]

    nome = pessoa["nome"]
    if random.random() < 0.30:
        nome = abreviar_nome_do_meio(pessoa)

    if random.random() < 0.20:
        endereco = pessoa["endereco_antigo"]
    else:
        endereco = pessoa["endereco"]

    return {
        "id_cliente": f"SG-{seq:05d}",
        "nome": nome,
        "cpf": cpf,
        "data_nascimento": pessoa["data_nascimento"].strftime("%d/%m/%Y"),
        "email": talvez_sujar_email(pessoa["email"]) if sorteio < 0.20 else talvez_sujar_email(pessoa["email_alternativo"]),
        "telefone": pessoa["telefone"],
        "endereco": endereco,
    }


def salvar_csv(caminho, linhas):
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=linhas[0].keys())
        writer.writeheader()
        writer.writerows(linhas)


def main():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    PASTA_GABARITO.mkdir(parents=True, exist_ok=True)

    pessoas = gerar_pessoas(N_PESSOAS)

    contadores = {"conta_corrente": 0, "cartoes": 0, "seguros": 0}
    registros = {"conta_corrente": [], "cartoes": [], "seguros": []}
    gabarito = []

    def registrar(origem, registro, pessoa):
        registros[origem].append(registro)
        gabarito.append({
            "origem": origem,
            "id_origem": registro["id_cliente"],
            "id_pessoa": pessoa["id_pessoa"],
        })

    for pessoa in pessoas:
        # Primeiro sorteia a presença nos três sistemas
        em_conta = random.random() < 0.90
        em_cartoes = random.random() < 0.60
        em_seguros = random.random() < 0.40

        # Garante que a pessoa esteja em pelo menos um
        if not (em_conta or em_cartoes or em_seguros):
            em_conta = True

        if em_conta:
            contadores["conta_corrente"] += 1
            registro = montar_conta_corrente(pessoa, contadores["conta_corrente"])
            registrar("conta_corrente", registro, pessoa)

        if em_cartoes:
            contadores["cartoes"] += 1
            registro = montar_cartoes(pessoa, contadores["cartoes"])
            registrar("cartoes", registro, pessoa)

        if em_seguros:
            contadores["seguros"] += 1
            registro = montar_seguros(pessoa, contadores["seguros"])
            registrar("seguros", registro, pessoa)

    for origem, linhas in registros.items():
        salvar_csv(PASTA_SAIDA / f"{origem}.csv", linhas)
        print(f"{origem}: {len(linhas)} registros")

    salvar_csv(PASTA_GABARITO / "gabarito.csv", gabarito)
    print(f"gabarito: {len(gabarito)} linhas")

if __name__ == "__main__":
    main()