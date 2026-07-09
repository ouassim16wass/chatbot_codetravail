import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, extname, join, normalize } from "node:path";

const racine = dirname(fileURLToPath(import.meta.url));
const dossierSite = join(racine, "site");

const env = await readFile(join(racine, "..", ".env"), "utf-8").catch(() => "");
for (const ligne of env.split(/\r?\n/)) {
  const m = ligne.match(/^([A-Z_]+)=(.*)$/);
  if (m && !process.env[m[1]]) process.env[m[1]] = m[2].trim();
}


const { default: ask } = await import("./functions/ask.mjs");

const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

createServer(async (req, res) => {
  if (req.url === "/api/ask" && req.method === "POST") {
    let corps = "";
    for await (const morceau of req) corps += morceau;
    const reponse = await ask(
      new Request("http://localhost/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: corps,
      })
    );
    res.writeHead(reponse.status, { "Content-Type": "application/json" });
    res.end(await reponse.text());
    return;
  }
  const chemin = normalize(
    join(dossierSite, req.url === "/" ? "index.html" : req.url.split("?")[0])
  );
  if (!chemin.startsWith(dossierSite)) {
    res.writeHead(403);
    res.end();
    return;
  }
  try {
    const contenu = await readFile(chemin);
    res.writeHead(200, {
      "Content-Type": types[extname(chemin)] || "application/octet-stream",
    });
    res.end(contenu);
  } catch {
    res.writeHead(404);
    res.end("introuvable");
  }
}).listen(8888, () => {
  console.log(
    `Serveur local : http://localhost:8888`
  );
});
