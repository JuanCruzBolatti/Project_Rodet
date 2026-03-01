const btn = document.getElementById("btn");
const out = document.getElementById("out");

btn.addEventListener("click", async () => {
  out.textContent = "Cargando...";
  const res = await fetch("/api/health");
  const data = await res.json();
  out.textContent = JSON.stringify(data, null, 2);
});