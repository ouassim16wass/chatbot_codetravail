import { pipeline } from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.3.1";

const etat = document.getElementById("etat");
const conversation = document.getElementById("conversation");
const champQuestion = document.getElementById("champ-question");
const boutonQuestion = document.getElementById("bouton-question");

const SEUIL_CONFIANCE = 0.5;

let base = null;
let normes = null;
let encoder = null;

function ajouterMessage(texte, classe) {
  const bloc = document.createElement("div");
  bloc.className = `message ${classe}`;
  bloc.textContent = texte;
  conversation.appendChild(bloc);
  bloc.scrollIntoView({ behavior: "smooth", block: "end" });
  return bloc;
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

function numerosCites(question) {
  const numeros = [];
  for (const m of question.matchAll(/[Ll]\.?\s*(\d{3,4}-\d+(?:-\d+)*)/g)) {
    numeros.push("L" + m[1]);
  }
  return numeros;
}

const MOTS_VIDES = new Set([
  "quelle", "quelles", "quels", "comment", "combien", "pendant", "apres",
  "avant", "entre", "cette", "votre", "notre", "salarie", "salariee",
  "employeur", "travail", "contrat", "france", "conditions", "regles",
]);

function motsCles(texte) {
  const mots = texte.toLowerCase().match(/[a-zà-ÿ]{6,}/g) || [];
  return mots.filter((m) => !MOTS_VIDES.has(m)).slice(0, 4);
}

async function chercherExtraits(question, sousQuestions) {
  const parNumero = new Map();
  for (const numero of numerosCites(question)) {
    const element = base.elements.find((e) => e.numero === numero);
    if (element) parNumero.set(numero, { element, score: 1.0 });
  }
  for (const sousQuestion of sousQuestions) {
    const sortie = await encoder(sousQuestion, { pooling: "mean" });
    const vecteur = Array.from(sortie.data);
    const normeQ = norme(vecteur);
    const scores = base.elements.map((element, i) => ({
      element,
      score: similarite(vecteur, normeQ, element.vecteur, normes[i]),
    }));
    scores.sort((a, b) => b.score - a.score);
    const candidats = scores.slice(0, 4);
    for (const mot of motsCles(sousQuestion)) {
      candidats.push(
        ...scores
          .filter((s) => s.element.texte.toLowerCase().includes(mot))
          .slice(0, 2)
      );
    }
    for (const candidat of candidats) {
      const numero = candidat.element.numero;
      const existant = parNumero.get(numero);
      if (!existant || candidat.score > existant.score) {
        parNumero.set(numero, candidat);
      }
    }
  }
  const limite = sousQuestions.length > 1 ? 8 : 6;
  return [...parNumero.values()]
    .sort((a, b) => b.score - a.score)
    .slice(0, limite)
    .map(({ element, score }) => ({
      numero: element.numero,
      date: element.date,
      texte: element.texte,
      score,
    }));
}

function panneauExtraits(extraits) {
  const details = document.createElement("details");
  details.className = "extraits";
  const resume = document.createElement("summary");
  resume.textContent = `Voir les ${extraits.length} articles trouves par la recherche`;
  details.appendChild(resume);
  for (const extrait of extraits) {
    const bloc = document.createElement("div");
    bloc.className = "extrait";
    const entete = document.createElement("strong");
    entete.textContent =
      `${extrait.numero} — en vigueur depuis le ${extrait.date} — ` +
      `pertinence ${(extrait.score * 100).toFixed(0)} %`;
    const texte = document.createElement("p");
    texte.textContent = extrait.texte;
    bloc.appendChild(entete);
    bloc.appendChild(texte);
    details.appendChild(bloc);
  }
  return details;
}

async function appeler(corps) {
  const reponse = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corps),
  });
  const donnees = await reponse.json();
  return { ok: reponse.ok, donnees };
}

async function initialiser() {
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
  const attente = ajouterMessage("Restructuration de la question...", "reponse");

  try {
    const preparation = await appeler({ action: "preparer", question });
    if (!preparation.ok) {
      attente.className = "message blocage";
      attente.textContent = preparation.donnees.erreur || "Erreur du serveur.";
      return;
    }
    if (preparation.donnees.verdict !== "legitime") {
      attente.className = "message blocage";
      attente.textContent = preparation.donnees.reponse;
      return;
    }

    const sousQuestions = preparation.donnees.sous_questions;
    if (sousQuestions.length > 1 || sousQuestions[0] !== question) {
      const reformulation = document.createElement("div");
      reformulation.className = "reformulation";
      reformulation.textContent =
        "Recherche effectuee avec : " + sousQuestions.join(" | ");
      attente.before(reformulation);
    }

    attente.textContent = "Recherche des articles pertinents...";
    const extraits = await chercherExtraits(question, sousQuestions);
    attente.before(panneauExtraits(extraits));

    attente.textContent = "Redaction de la reponse...";
    const generation = await appeler({ action: "repondre", question, extraits });
    if (!generation.ok) {
      attente.className = "message blocage";
      attente.textContent = generation.donnees.erreur || "Erreur du serveur.";
      return;
    }

    attente.innerHTML = rendreMarkdown(generation.donnees.reponse);
    const sources = document.createElement("div");
    sources.className = "sources";
    sources.textContent =
      "Articles sources : " + generation.donnees.sources.join(", ");
    attente.appendChild(sources);
    const confiance = Math.max(...extraits.map((e) => e.score), 0);
    if (confiance < SEUIL_CONFIANCE) {
      const alerte = document.createElement("div");
      alerte.className = "alerte";
      alerte.textContent =
        "Attention : correspondance faible avec le corpus, la reponse peut etre incomplete.";
      attente.appendChild(alerte);
    }
    const mentions = document.createElement("div");
    mentions.className = "mentions";
    mentions.textContent =
      `Corpus a jour au ${base.date_corpus} - le droit du travail evolue, ` +
      `verifiez sur legifrance.gouv.fr. ${generation.donnees.avertissement}`;
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

boutonQuestion.addEventListener("click", poser);
champQuestion.addEventListener("keydown", (e) => {
  if (e.key === "Enter") poser();
});

initialiser();
