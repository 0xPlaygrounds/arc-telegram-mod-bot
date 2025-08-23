const BASE_URL = "http://127.0.0.1:8080";

export async function fetchMessages() {
  const res = await fetch(`${BASE_URL}/messages`);
  return await res.json();
}

export async function updateLabel(msgId, label) {
  const res = await fetch(`${BASE_URL}/label/${msgId}/${label}`, {
    method: "POST"
  });
  return await res.json();
}
