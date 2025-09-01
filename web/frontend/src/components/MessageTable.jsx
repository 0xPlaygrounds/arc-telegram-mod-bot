import { useState, useEffect } from "react";
import { updateLabel, fetchMessages, updateBlocklistStatus } from "../api";

const LABELS = [
  { name: "Safe", color: "#98ff98" },
  { name: "Spam", color: "#F44336" },
  { name: "Review", color: "#FFC107" },
];

const PAGE_SIZE = 20;

export default function MessageTable({ messages, refreshMessages }) {
  const [messagesData, setMessagesData] = useState({
    messages: [],
    total_count: 0,
  });
  const [page, setPage] = useState(1);
  const [expandedMessages, setExpandedMessages] = useState({});
  const [openDropdownId, setOpenDropdownId] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: null, direction: "asc" });
  const [updatingBlocklist, setUpdatingBlocklist] = useState(false);

  const totalPages = Math.ceil(messagesData.total_count / PAGE_SIZE);

  const fetchPageData = async (
    pageNum = 1,
    sortKey = sortConfig.key || "timestamp_message",
    sortDirection = sortConfig.direction || "desc"
  ) => {
    try {
      const res = await fetchMessages(pageNum, PAGE_SIZE, sortKey, sortDirection);
      setMessagesData(res);
    } catch (error) {
      console.error("Error fetching messages:", error);
    }
  };

  // Initial fetch and when page/sort changes
  useEffect(() => {
    fetchPageData(page);
  }, [page, sortConfig]);

  // whenever parent messages prop changes, update local state
  useEffect(() => {
    setMessagesData((prev) => ({ ...prev, messages: messages || [] }));
  }, [messages]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (refreshMessages) refreshMessages();
    }, 300000);

    return () => clearInterval(interval);
  }, [refreshMessages]);

  const handleLabelClick = (id) =>
    setOpenDropdownId(openDropdownId === id ? null : id);

  const handleLabelSelect = async (msgId, label) => {
    await updateLabel(msgId, label);
    setOpenDropdownId(null);
    fetchPageData(page); // refresh after label change
  };

  const handleSort = (key) => {
    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  const toggleMessageExpansion = (id) =>
    setExpandedMessages((prev) => ({ ...prev, [id]: !prev[id] }));

  const formatCST = (utcDateStr) => {
    const date = new Date(utcDateStr);
    const cstOffset = -5;
    const cstDate = new Date(date.getTime() + cstOffset * 60 * 60 * 1000);
    return cstDate.toLocaleString();
  };

  const MAX_CHARS = 50;

  return (
    <div>
      <div
        style={{
          overflowX: "auto",
          overflowY: "auto",
          maxHeight: "80vh",
          width: "100%",
          borderRadius: "12px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
          backgroundColor: "#1b1c1f",
        }}
      >
        <table
          style={{
            width: "100%",
            borderCollapse: "separate",
            borderSpacing: 0,
          }}
        >
          <thead>
            <tr>
              {[
                { label: "ID", key: "id" },
                { label: "Timestamp (CST)", key: "timestamp_message" },
                { label: "User", key: "username" },
                { label: "Message", key: "text" },
                { label: "Label", key: "label" },
                { label: "Review Status", key: "review_status" },
                { label: "Usage Count", key: "usage_count" },
                { label: "AI Prediction", key: "ai_prediction" },
                { label: "Confidence", key: "ai_confidence" },
                { label: "Reviewer", key: "reviewed_by" },
                { label: "Blocklist", key: "blocklist_status" },
              ].map((col) => (
                <th
                  key={col.key}
                  onClick={() => handleSort(col.key)}
                  style={{ cursor: "pointer", whiteSpace: "nowrap" }}
                >
                  {col.label}{" "}
                  <span style={{ display: "inline-block", width: "1em", textAlign: "center" }}>
                    {sortConfig.key === col.key ? (sortConfig.direction === "asc" ? "↑" : "↓") : ""}
                  </span>
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {messagesData.messages.map((msg) => {
              const currentLabel = LABELS.find((l) => l.name === msg.label);
              const isExpanded = expandedMessages[msg.id];
              const displayedText =
                msg.text.length > MAX_CHARS && !isExpanded
                  ? msg.text.slice(0, MAX_CHARS) + "..."
                  : msg.text;

              return (
                <tr key={msg.id}>
                  <td>{msg.id}</td>
                  <td>{formatCST(msg.timestamp_message)}</td>
                  <td>{msg.username}</td>
                  <td>
                    {displayedText}{" "}
                    {msg.text.length > MAX_CHARS && (
                      <button
                        onClick={() => toggleMessageExpansion(msg.id)}
                        style={{
                          background: "none",
                          border: "none",
                          color: "#007bff",
                          cursor: "pointer",
                          padding: 0,
                          marginLeft: "5px",
                        }}
                      >
                        {isExpanded ? "Show Less" : "Show More"}
                      </button>
                    )}
                  </td>
                  <td style={{ position: "relative" }}>
                    {msg.label === null ? (
                      <div style={{ display: "flex", gap: "4px" }}>
                        {LABELS.map((label) => (
                          <button
                            key={label.name}
                            style={{
                              backgroundColor: label.color,
                              color: label.name === "Safe" ? "#000" : "#fff",
                              borderRadius: "6px",
                              padding: "4px 8px",
                              border: "none",
                              cursor: "pointer",
                            }}
                            onClick={() => handleLabelSelect(msg.id, label.name)}
                          >
                            {label.name}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div>
                        <button
                          style={{
                            backgroundColor: currentLabel?.color || "#98ff98",
                            color: msg.label === "Safe" ? "#000" : "#fff",
                            borderRadius: "6px",
                            padding: "4px 8px",
                            border: "none",
                            cursor: "pointer",
                          }}
                          onClick={() => handleLabelClick(msg.id)}
                        >
                          {msg.label}
                        </button>
                        {openDropdownId === msg.id && (
                          <div
                            style={{
                              position: "absolute",
                              top: "100%",
                              left: 0,
                              background: "#fff",
                              borderRadius: "6px",
                              overflow: "hidden",
                              border: "1px solid #ccc",
                              zIndex: 1000,
                            }}
                          >
                            {LABELS.map((label) => (
                              <div
                                key={label.name}
                                style={{
                                  padding: "5px 10px",
                                  backgroundColor: label.color,
                                  color: label.name === "Safe" ? "#000" : "#fff",
                                  cursor: "pointer",
                                }}
                                onClick={() => handleLabelSelect(msg.id, label.name)}
                              >
                                {label.name}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </td>
                  <td>{msg.review_status}</td>
                  <td>{msg.usage_count}</td>
                  <td>{msg.ai_prediction || "-"}</td>
                  <td>
                    {msg.ai_confidence != null
                      ? (msg.ai_confidence * 100).toFixed(1) + "%"
                      : "-"}
                  </td>
                  <td>{msg.reviewed_by || "Red Candle God"}</td>
                  <td>
                    {msg.blocklist_status ? (
                      <span style={{ color: "#F44336", fontWeight: "bold" }}>
                        {msg.blocklist_status.charAt(0).toUpperCase() +
                          msg.blocklist_status.slice(1)}
                      </span>
                    ) : (
                      <span>-</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div
        style={{
          marginTop: "20px",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: "15px",
          flexWrap: "wrap",
          color: "#ccc",
          fontSize: "0.95rem",
        }}
      >
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: page === 1 ? "#555" : "#007bff",
            color: "#fff",
            cursor: page === 1 ? "not-allowed" : "pointer",
            transition: "all 0.2s",
          }}
        >
          Prev
        </button>

        <span>
          Page <strong>{page}</strong> of <strong>{totalPages}</strong> | 
          Showing <strong>
            {messagesData.messages.length > 0
              ? `${(page - 1) * PAGE_SIZE + 1} – ${Math.min(
                  (page - 1) * PAGE_SIZE + PAGE_SIZE,
                  messagesData.total_count
                )}`
              : 0}
          </strong> of <strong>{messagesData.total_count}</strong> records
        </span>

        <button
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page === totalPages}
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            border: "none",
            backgroundColor: page === totalPages ? "#555" : "#007bff",
            color: "#fff",
            cursor: page === totalPages ? "not-allowed" : "pointer",
            transition: "all 0.2s",
          }}
        >
          Next
        </button>
      </div>
    </div>
  );
}
