import { pipeline } from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.3.1";

const porte = document.getElementById("porte");
const app = document.getElementById("app");
const champCode = document.getElementById("champ-code");
const boutonCode = document.getElementById("bouton-code");
const erreurCode = document.getElementById("erreur-code");
const etat = document.getElementById("etat");
const conversation = document.getElementById("conversation");
const champQuestion = document.getElementById("champ-question");
const boutonQuestion = document.getElementById("bouton-question");

let codeAcces = sessionStorage.getItem("code_acces") || "";
let base = null;
let normes = null;
let encoder = null;

function afficher(element) {
  element.classList.remove("cache");
}

function masquer(element) {
  element.classList.add("cache");
}

function ajouterMessage(texte, classe) {
  const bloc = document.createElement("div");
  bloc.className = `message ${classe}`;
  bloc.textContent = texte;
  conversation.appendChild(bloc);
  bloc.scrollIntoView({ behavior: "smooth", block: "end" });
  return bloc;
}

function norme(vecteur) {
  let somme = 0;
  for (const v of vecteur) somme += v * v;
  return Math.sqrt(somme);
}

function similarite(a, normeA, b, normeB) {
  let produit = 0;
  for (let i = 0; i < a.length; i++) produit += a[i] * b[i];
  return produit / (normeA * normeB || 1);
}

function rendreMarkdown(texte) {
  const echappe = texte
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  return echappe
    .replace(/^#{1,4} (.*)$/gm, "<strong>$1</strong>")
    .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
    .replace(/^\s*[-*] /gm, "• ");
}


function numerosCites(question) {
  const numeros = [];
  for (const m of question.matchAll(/[Ll]\.?\s*(\d{3,4}-\d+(?:-\d+)*)/g)) {
    numeros.push("L" + m[1]);
  }
  return numeros;
}

function rechercher(vecteurQuestion, question) {
  const normeQ = norme(vecteurQuestion);
  const cites = numerosCites(question);
  const scores = base.elements.map((element, i) => ({
    element,
    score: cites.includes(element.numero)
      ? 1.0
      : similarite(vecteurQuestion, normeQ, element.vecteur, normes[i]),
  }));
  scores.sort((a, b) => b.score - a.score);
  const retenus = [];
  const vus = new Set();
  for (const { element } of scores) {
    if (vus.has(element.numero)) continue;
    vus.add(element.numero);
    retenus.push({ numero: element.numero, texte: element.texte });
    if (retenus.length === 6) break;
  }
  return retenus;
}

async function initialiser() {
  masquer(porte);
  afficher(app);
  try {
    etat.textContent = "Chargement de la base documentaire...";
    const reponse = await fetch("data/base.json");
    base = await reponse.json();
    normes = base.elements.map((e) => norme(e.vecteur));
    etat.textContent =
      "Telechargement du modele de recherche (une seule fois, environ 50 Mo)...";
    encoder = await pipeline(
      "feature-extraction",
      "Xenova/paraphrase-multilingual-MiniLM-L12-v2"
    );
    etat.textContent = `Pret. Corpus a jour au ${base.date_corpus}.`;
    champQuestion.disabled = false;
    boutonQuestion.disabled = false;
    champQuestion.focus();
  } catch (e) {
    etat.textContent = "Erreur de chargement : " + e.message;
  }
}

async function poser() {
  const question = champQuestion.value.trim();
  if (!question || !encoder) return;
  champQuestion.value = "";
  champQuestion.disabled = true;
  boutonQuestion.disabled = true;
  ajouterMessage(question, "question");
  const attente = ajouterMessage("Recherche des articles pertinents...", "reponse");

  try {
    const sortie = await encoder(question, { pooling: "mean" });
    const extraits = rechercher(Array.from(sortie.data), question);
    attente.textContent = "Redaction de la reponse...";

    const reponse = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code: codeAcces, question, extraits }),
    });
    const donnees = await reponse.json();

    if (!reponse.ok) {
      attente.className = "message blocage";
      attente.textContent = donnees.erreur || "Erreur du serveur.";
      if (reponse.status === 401) {
        sessionStorage.removeItem("code_acces");
        codeAcces = "";
        champCode.value = "";
        erreurCode.textContent = "Code d'acces invalide, reessayez.";
        masquer(app);
        afficher(porte);
      }
      return;
    }

    if (donnees.verdict !== "legitime") {
      attente.className = "message blocage";
      attente.textContent = donnees.reponse;
      return;
    }

    attente.innerHTML = rendreMarkdown(donnees.reponse);
    const sources = document.createElement("div");
    sources.className = "sources";
    sources.textContent = "Articles sources : " + donnees.sources.join(", ");
    attente.appendChild(sources);
    const mentions = document.createElement("div");
    mentions.className = "mentions";
    mentions.textContent =
      `Corpus a jour au ${base.date_corpus} - le droit du travail evolue, ` +
      `verifiez sur legifrance.gouv.fr. ${donnees.avertissement}`;
    attente.appendChild(mentions);
  } catch (e) {
    attente.className = "message blocage";
    attente.textContent = "Erreur : " + e.message;
  } finally {
    champQuestion.disabled = false;
    boutonQuestion.disabled = false;
    champQuestion.focus();
  }
}

boutonCode.addEventListener("click", () => {
  const code = champCode.value.trim();
  if (!code) {
    erreurCode.textContent = "Entrez un code d'acces.";
    return;
  }
  codeAcces = code;
  sessionStorage.setItem("code_acces", code);
  initialiser();
});

champCode.addEventListener("keydown", (e) => {
  if (e.key === "Enter") boutonCode.click();
});

boutonQuestion.addEventListener("click", poser);
champQuestion.addEventListener("keydown", (e) => {
  if (e.key === "Enter") poser();
});

if (codeAcces) initialiser();
