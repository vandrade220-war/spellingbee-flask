from flask import Flask, render_template, request, redirect, url_for, session
import random
import unicodedata
import os
import logging
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "amor"  # necessário para usar sessão

# Configurações de sessão
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Definindo o tempo de expiração

# --------------------------------------------
# Utilitários
# --------------------------------------------

def normalizar(palavra: str) -> str:
    """Remove acentos e coloca em minúsculas."""
    nfkd = unicodedata.normalize("NFKD", palavra)
    sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sem_acento.lower()


def carregar_palavras(caminho_arquivo: str = "palavras.txt"):
    """
    Carrega palavras de um arquivo (uma por linha).
    Se não existir, usa uma lista interna.
    """
    if os.path.exists(caminho_arquivo):
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            palavras = [normalizar(l.strip()) for l in f if l.strip()]
    else:
        palavras = [
            "Cacto", "Ciclo", "Cena", "Cerca", "Capaz", "Chave", "Custo"
        ]
        palavras = [normalizar(p) for p in palavras]

    return [p for p in palavras if len(p) >= 4]


def palavras_validas_para_tabuleiro(palavras, letras, letra_central, tamanho_min=4):
    conjunto = set(letras)
    validas = []
    for p in palavras:
        if len(p) < tamanho_min:
            continue
        if letra_central not in p:
            continue
        if any(c not in conjunto for c in p):
            continue
        validas.append(p)
    return sorted(set(validas))


def gerar_tabuleiro(palavras, tamanho_min=4, tentativas=200):
    """
    Gera 7 letras, escolhe uma central e calcula as soluções possíveis.
    Tenta achar um conjunto com pelo menos 10 palavras.
    """
    for _ in range(tentativas):
        base = random.choice(palavras)
        letras_unicas = sorted(set(base))

        if len(letras_unicas) < 7:
            # tenta completar com outras palavras
            while len(letras_unicas) < 7:
                outra = random.choice(palavras)
                for c in set(outra):
                    if c.isalpha() and c not in letras_unicas:
                        letras_unicas.append(c)
                    if len(letras_unicas) == 7:
                        break

        if len(letras_unicas) != 7:
            continue

        random.shuffle(letras_unicas)
        letra_central = random.choice(letras_unicas)

        solucao = palavras_validas_para_tabuleiro(
            palavras, letras_unicas, letra_central, tamanho_min
        )

        if len(solucao) >= 10:
            return letras_unicas, letra_central, solucao


def pontuacao_palavra(p: str) -> int:
    """Regras simples de pontuação."""
    if len(p) == 4:
        return 1
    elif len(p) == 5:
        return 2
    elif len(p) == 6:
        return 3
    else:
        return 4


# --------------------------------------------
# Rotas
# --------------------------------------------

@app.route("/")
def index():
    # Verifica se 'letras' está presente na sessão, senão chama a função iniciar_novo_jogo
    if "letras" not in session:
        iniciar_novo_jogo()  # Inicializa os dados da sessão

    letras = session["letras"]
    letra_central = session["letra_central"]
    usadas = session.get("usadas", [])
    pontuacao = session.get("pontuacao", 0)
    mensagem = session.pop("mensagem", "")
    tipo_mensagem = session.pop("tipo_mensagem", "info")
    total_possiveis = len(session.get("solucao", []))

    # Pega as 6 letras de fora (tira a central, corta em 6 no máximo)
    outer_letras = [l for l in letras if l != letra_central][:6]

    return render_template(
        "index.html",
        letras=letras,
        letra_central=letra_central,
        outer_letras=outer_letras,
        usadas=usadas,
        pontuacao=pontuacao,
        mensagem=mensagem,
        tipo_mensagem=tipo_mensagem,
        total_possiveis=total_possiveis,
    )


def iniciar_novo_jogo():
    palavras = carregar_palavras()
    resultado = gerar_tabuleiro(palavras)
    
    if resultado is None:
        session["mensagem"] = "Não foi possível gerar um tabuleiro válido. Tente novamente."
        session["tipo_mensagem"] = "erro"
        logging.error("Não foi possível gerar um tabuleiro válido após várias tentativas.")
        return redirect(url_for("index"))
    
    letras, letra_central, solucao = resultado
    session["letras"] = letras
    session["letra_central"] = letra_central
    session["solucao"] = solucao
    session["usadas"] = []
    session["pontuacao"] = 0
    logging.info(f"Novo jogo iniciado: letras={letras}, letra central={letra_central}")


@app.route("/novo")
def novo_jogo():
    iniciar_novo_jogo()
    session["mensagem"] = "Novo jogo iniciado!"
    session["tipo_mensagem"] = "info"
    return redirect(url_for("index"))


@app.route("/tentar", methods=["POST"])
def tentar():
    palavra_bruta = request.form.get("palavra", "").strip()
    if not palavra_bruta:
        session["mensagem"] = "Digite uma palavra."
        session["tipo_mensagem"] = "erro"
        return redirect(url_for("index"))

    if "letras" not in session:
        iniciar_novo_jogo()

    palavra = normalizar(palavra_bruta)
    letras = session["letras"]
    letra_central = session["letra_central"]
    solucao = session["solucao"]
    usadas = session.get("usadas", [])
    pontuacao = session.get("pontuacao", 0)

    # Validações
    if len(palavra) < 4:
        session["mensagem"] = "A palavra precisa ter pelo menos 4 letras."
        session["tipo_mensagem"] = "erro"
    elif any(not c.isalpha() for c in palavra):
        session["mensagem"] = "Use apenas letras (sem números ou símbolos)."
        session["tipo_mensagem"] = "erro"
    elif letra_central not in palavra:
        session["mensagem"] = f"A palavra precisa conter a letra central '{letra_central}'."
        session["tipo_mensagem"] = "erro"
    elif any(c not in letras for c in palavra):
        session["mensagem"] = f"Use apenas as letras: {', '.join(letras)}."
        session["tipo_mensagem"] = "erro"
    elif palavra in usadas:
        session["mensagem"] = "Você já usou essa palavra."
        session["tipo_mensagem"] = "erro"
    elif palavra not in solucao:
        session["mensagem"] = "Palavra não está no dicionário deste jogo (ou não é válida)."
        session["tipo_mensagem"] = "erro"
    else:
        # OK
        usadas.append(palavra)
        pontos = pontuacao_palavra(palavra)
        pontuacao += pontos
        session["usadas"] = usadas
        session["pontuacao"] = pontuacao
        session["mensagem"] = f"Boa! '{palavra}' vale {pontos} ponto(s)."
        session["tipo_mensagem"] = "sucesso"

    return redirect(url_for("index"))


@app.route("/revelar")
def revelar():
    solucao = session.get("solucao", [])
    session["mensagem"] = "Soluções: " + ", ".join(solucao)
    session["tipo_mensagem"] = "info"
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Executar em modo debug durante desenvolvimento
    app.run(debug=True)
