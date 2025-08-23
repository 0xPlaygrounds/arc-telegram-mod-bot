const BASE_URL = "http://127.0.0.1:8080";

/**
 * Fetch messages from backend with pagination
 */
export async function fetchMessages(page = 1, page_size = 20) {
  try {
    const res = await fetch(
      `${BASE_URL}/messages?page=${page}&page_size=${page_size}`
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json(); // should return { messages, page, page_size, total_count }
  } catch (err) {
    console.error("Fetch failed:", err);
    return { messages: [], page, page_size, total_count: 0 };
  }
}

/**
 * Update the label for a message
 */
export async function updateLabel(msgId, label) {
  const reviewerUsername = "Red Candle God";
  const res = await fetch(
    `${BASE_URL}/label/${msgId}/${label}?reviewer_username=${encodeURIComponent(reviewerUsername)}`,
    { method: "POST" }
  );
  return await res.json();
}
