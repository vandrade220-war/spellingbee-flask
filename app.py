from flask import Flask, render_template, request, session, jsonify

app = Flask(__name__)
app.config["SECRET_KEY"] = "troque-esta-string"

# ---------- CONFIG DO DESAFIO ----------

PUZZLE = {
    "center": "h",
    # todas as letras disponíveis no jogo (inclui a central)
    "letters": list("hamptuc")
}

# Mini dicionário de exemplo (pode adicionar mais palavras aqui)
WORD_LIST = [
    "chap", "chat", "math", "match", "hatch",
    "hutch", "hump", "humph", "much", "thatch"
]

LETTERS_SET = set(PUZZLE["letters"])


def passes_basic_rules(word: str):
    """Verifica regras básicas sem olhar o dicionário."""
    if len(word) < 4:
        return False, "A palavra precisa ter pelo menos 4 letras."
    if PUZZLE["center"] not in word:
        return False, f"A palavra precisa usar a letra central: {PUZZLE['center'].upper()}."
    if not set(word) <= LETTERS_SET:
        return False, "Você usou letras que não fazem parte do jogo."
    return True, ""


def is_pangram(word: str) -> bool:
    """Usa todas as letras pelo menos uma vez?"""
    return LETTERS_SET <= set(word)


# Filtra o dicionário para esta combinação de letras
VALID_WORDS = [
    w for w in WORD_LIST if passes_basic_rules(w)[0]
]

PANGRAMS = [w for w in VALID_WORDS if is_pangram(w)]


def word_score(word: str) -> int:
    """Regra de pontuação."""
    n = len(word)
    points = 1 if n == 4 else n
    if is_pangram(word):
        points += 7
    return points


MAX_SCORE = sum(word_score(w) for w in VALID_WORDS)


def rating_for(score: int) -> str:
    """Classificação simples baseada no percentual do score máximo."""
    if not MAX_SCORE:
        return "Jogador"
    ratio = score / MAX_SCORE
    if ratio < 0.15:
        return "Beginner"
    elif ratio < 0.35:
        return "Good Start"
    elif ratio < 0.60:
        return "Moving Up"
    elif ratio < 0.90:
        return "Excellent"
    else:
        return "Genius"


# ---------- ROTAS ----------

@app.route("/")
def index():
    # inicializa sessão
    session.setdefault("score", 0)
    session.setdefault("found", [])
    outer_letters = [l for l in PUZZLE["letters"] if l != PUZZLE["center"]]
    return render_template(
        "index.html",
        center=PUZZLE["center"],
        outer_letters=outer_letters,
        score=session["score"],
        rating=rating_for(session["score"]),
        pangrams=PANGRAMS,
    )


@app.post("/submit")
def submit_word():
    data = request.get_json() or {}
    word = (data.get("word") or "").strip().lower()

    score = session.get("score", 0)
    found = session.get("found", [])

    if not word:
        return jsonify(ok=False, message="Digite uma palavra.", score=score,
                       rating=rating_for(score))

    if word in found:
        return jsonify(ok=False, message="Você já encontrou essa palavra.",
                       score=score, rating=rating_for(score))

    ok, msg = passes_basic_rules(word)
    if not ok:
        return jsonify(ok=False, message=msg, score=score,
                       rating=rating_for(score))

    if word not in VALID_WORDS:
        return jsonify(
            ok=False,
            message="Essa palavra não está na nossa lista (ou é obscura/propriedade/não permitida).",
            score=score,
            rating=rating_for(score),
        )

    pts = word_score(word)
    score += pts
    found.append(word)

    session["score"] = score
    session["found"] = found

    return jsonify(
        ok=True,
        message=f"+{pts} ponto(s)!",
        score=score,
        rating=rating_for(score),
        word=word,
        points=pts,
        pangram=is_pangram(word),
    )


if __name__ == "__main__":
    app.run(debug=True)
