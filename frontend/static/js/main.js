// static/js/main.js
// shared helper functions (JWT + fetch helpers)

const apiBase = "http://127.0.0.1:5000";

async function apiFetch(path, options = {}){
  // Adds Authorization header automatically if token exists
  const token = localStorage.getItem("token");
  const headers = options.headers || {};
  headers["Content-Type"] = headers["Content-Type"] || "application/json";
  if(token) headers["Authorization"] = "Bearer " + token;
  options.headers = headers;

  const res = await fetch(apiBase + path, options);
  return res;
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "login.html";
}

