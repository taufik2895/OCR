const api = "/api/v1";
const form = document.querySelector("#upload-form");
const fileInput = document.querySelector("#file");
const statusBox = document.querySelector("#status");

fileInput.addEventListener("change", () => {
  document.querySelector("#file-label").textContent = fileInput.files[0]?.name || "Choose document";
});

async function jsonRequest(url, options = {}) {
  const response = await fetch(url, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Request failed (${response.status})`);
  return body;
}

async function refresh() {
  const [dashboard, documents] = await Promise.all([
    jsonRequest(`${api}/dashboard`), jsonRequest(`${api}/documents?limit=100`)
  ]);
  document.querySelector("#total").textContent = dashboard.total;
  document.querySelector("#completed").textContent = dashboard.completed;
  document.querySelector("#failed").textContent = dashboard.failed;
  document.querySelector("#confidence").textContent = `${Math.round(dashboard.average_confidence * 100)}%`;
  document.querySelector("#history").innerHTML = documents.map(item => `
    <tr><td>${escapeHtml(item.filename)}</td><td class="status-${item.status}">${item.status}</td>
    <td>${item.provider || "-"}</td><td>${item.confidence == null ? "-" : `${Math.round(item.confidence * 100)}%`}</td>
    <td>${new Date(item.created_at).toLocaleString()}</td></tr>`).join("");
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = value;
  return node.innerHTML;
}

function showResult(result) {
  document.querySelector("#result-panel").classList.remove("hidden");
  document.querySelector("#result-meta").textContent = `${result.provider} | ${Math.round((result.confidence || 0) * 100)}% confidence${result.used_vlm ? " | VLM fallback" : ""}`;
  document.querySelector("#result-text").textContent = result.text;
  document.querySelector("#structured-data").textContent = JSON.stringify(result.extracted_fields, null, 2);
  document.querySelector("#exports").innerHTML = ["txt", "json", "csv", "xlsx"].map(format =>
    `<a href="${api}/documents/${result.document_id}/export/${format}">${format.toUpperCase()}</a>`
  ).join("");
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  statusBox.textContent = "Uploading...";
  try {
    const data = new FormData();
    data.append("file", fileInput.files[0]);
    const uploaded = await jsonRequest(`${api}/documents`, { method: "POST", body: data });
    statusBox.textContent = "Running OCR...";
    const fields = document.querySelector("#fields").value.split(",").map(value => value.trim()).filter(Boolean);
    const result = await jsonRequest(`${api}/documents/${uploaded.id}/process`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ structured_fields: fields })
    });
    showResult(result);
    statusBox.textContent = "Processing complete.";
    await refresh();
  } catch (error) {
    statusBox.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#refresh").addEventListener("click", () => refresh().catch(error => statusBox.textContent = error.message));
refresh().catch(error => statusBox.textContent = error.message);
