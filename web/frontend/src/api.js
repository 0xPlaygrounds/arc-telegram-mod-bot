const BASE_URL = "http://127.0.0.1:8080";

/**
 * Fetch messages from backend with pagination, sorting, and search
 */
export async function fetchMessages(
  page = 1,
  page_size = 20,
  sortKey = "timestamp_message",
  sortDirection = "desc",
  searchTerm = ""
) {
  try {
    const params = new URLSearchParams({
      page,
      page_size,
      sort_key: sortKey,
      sort_direction: sortDirection,
    });

    if (searchTerm && searchTerm.trim() !== "") {
      params.append("search", searchTerm.trim());
    }

    const res = await fetch(`${BASE_URL}/messages?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json(); // { messages, page, page_size, total_count, sort_key, sort_direction }
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
    `${BASE_URL}/label/${msgId}/${label}?reviewer_username=${encodeURIComponent(
      reviewerUsername
    )}`,
    { method: "POST" }
  );
  return await res.json();
}

/**
 * Update messages with blocklist status and optionally refresh messages
 * @param {Function} refreshCallback - optional function to call after updating
 */
export async function updateBlocklistStatus(refreshCallback) {
  try {
    const res = await fetch(`${BASE_URL}/update_blocklist_status`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json(); // { updated, checked }
    console.info("Blocklist update result:", data);

    // Refresh messages if callback provided
    if (refreshCallback && typeof refreshCallback === "function") {
      refreshCallback();
    }

    return data;
  } catch (err) {
    console.error("Blocklist status update failed:", err);
    return { updated: 0, checked: 0 };
  }
}
