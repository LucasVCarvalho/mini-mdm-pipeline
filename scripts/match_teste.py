import csv
from datetime import datetime


def ler_csv(caminho):
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def normalizar_email(email):
    return email.strip().lower()


def normalizar_data(data):
    # Aceita AAAA-MM-DD ou DD/MM/AAAA e devolve sempre AAAA-MM-DD
    if "/" in data:
        return datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")
    return data


def chave_match(registro):
    return (normalizar_email(registro["email"]), normalizar_data(registro["data_nascimento"]))


cartoes = ler_csv("data/fontes/cartoes.csv")
seguros = ler_csv("data/fontes/seguros.csv")

# Índice: uma passada pelos seguros, guardando cada um pela sua chave
indice_seguros = {}
for s in seguros:
    indice_seguros.setdefault(chave_match(s), []).append(s)

# Para cada cartão, uma consulta direta no índice
matches = []
for c in cartoes:
    for s in indice_seguros.get(chave_match(c), []):
        matches.append({
            "id_cartoes": c["id_cliente"],
            "id_seguros": s["id_cliente"],
            "nome_cartoes": c["nome"],
            "nome_seguros": s["nome"],
        })

print(f"{len(matches)} matches encontrados")
for m in matches[:5]:
    print(m)

# ---------- Avaliação com o gabarito (só em script de teste!) ----------
gabarito = ler_csv("data/gabarito/gabarito.csv")
pessoa_de = {g["id_origem"]: g["id_pessoa"] for g in gabarito}

em_cartoes = {g["id_pessoa"] for g in gabarito if g["origem"] == "cartoes"}
em_seguros = {g["id_pessoa"] for g in gabarito if g["origem"] == "seguros"}
pares_reais = len(em_cartoes & em_seguros)

corretos = sum(1 for m in matches if pessoa_de[m["id_cartoes"]] == pessoa_de[m["id_seguros"]])

print(f"Precisão: {corretos} de {len(matches)} matches estavam certos")
print(f"Recall: {corretos} de {pares_reais} pares reais foram encontrados")