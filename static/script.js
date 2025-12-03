const input = document.getElementById("wordInput");
const form = document.getElementById("wordForm");
const messageEl = document.getElementById("message");
const scoreEl = document.getElementById("score");
const ratingEl = document.getElementById("rating");
const foundList = document.getElementById("foundList");

const deleteBtn = document.getElementById("deleteBtn");
const enterBtn = document.getElementById("enterBtn");
const shuffleBtn = document.getElementById("shuffleBtn");

const outerButtons = Array.from(document.querySelectorAll(".hex.outer"));
const centerButton = document.querySelector(".hex.center");

// clicar nas letras
[centerButton, ...outerButtons].forEach(btn => {
  btn.addEventListener("click", () => {
    const letter = btn.dataset.letter;
    input.value += letter;
    input.focus();
  });
});

// deletar
deleteBtn.addEventListener("click", () => {
  input.value = input.value.slice(0, -1);
  input.focus();
});

// enviar
enterBtn.addEventListener("click", submitWord);
form.addEventListener("submit", e => {
  e.preventDefault();
  submitWord();
});

// embaralhar letras externas
shuffleBtn.addEventListener("click", () => {
  const letters = outerButtons.map(b => b.dataset.letter);
  for (let i = letters.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [letters[i], letters[j]] = [letters[j], letters[i]];
  }
  outerButtons.forEach((b, i) => {
    b.dataset.letter = letters[i];
    b.textContent = letters[i].toUpperCase();
  });
});

function submitWord() {
  const word = input.value.trim();
  if (!word) return;

  fetch("/submit", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({word})
  })
  .then(r => r.json())
  .then(data => {
    messageEl.textContent = data.message || "";
    scoreEl.textContent = data.score;
    ratingEl.textContent = data.rating;

    if (data.ok && data.word) {
      const li = document.createElement("li");
      li.textContent = data.word + (data.pangram ? " ★" : "");
      foundList.appendChild(li);
    }
    input.value = "";
    input.focus();
  })
  .catch(err => {
    console.error(err);
    messageEl.textContent = "Erro ao enviar palavra.";
  });
}

// permitir Enter pela tecla
input.addEventListener("keydown", e => {
  if (e.key === "Enter") {
    e.preventDefault();
    submitWord();
  }
});
