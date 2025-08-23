const BASE_URL = "http://127.0.0.1:8080";

/**
 * Fetch messages from backend
 */
export async function fetchMessages() {
  const res = await fetch(`${BASE_URL}/messages`);
  return await res.json();
}

/**
 * Update the label for a message
 * For now, reviewerUsername is hardcoded for simplicity.
 * Later, replace with the logged-in user's username from Firebase Auth.
 */
export async function updateLabel(msgId, label) {
  // TEMPORARY: hardcoded reviewer for all actions
  const reviewerUsername = "Red Candle God";

  // PRODUCTION (commented out for now):
  // const user = getCurrentUser(); // e.g., Firebase auth user
  // const reviewerUsername = user?.username || "Unknown";

  const res = await fetch(
    `${BASE_URL}/label/${msgId}/${label}?reviewer_username=${encodeURIComponent(reviewerUsername)}`,
    {
      method: "POST",
    }
  );

  return await res.json();
}
