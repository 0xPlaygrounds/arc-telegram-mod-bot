import { useState } from "react";
import { updateLabel } from "../api";

const LABELS = [
  { name: "Safe", color: "#98ff98" },
  { name: "Spam", color: "#F44336" },
  { name: "Review", color: "#FFC107" },
];

export default function MessageTable({ messages, refreshMessages }) {
  const [openDropdownId, setOpenDropdownId] = useState(null);

  const handleLabelClick = (id) => {
    setOpenDropdownId(openDropdownId === id ? null : id);
  };

  const handleLabelSelect = async (msgId, label) => {
    // No reviewer needed for now; handled in api.js as "Red Candle God"
    await updateLabel(msgId, label);
    setOpenDropdownId(null);
    refreshMessages();
  };

  return (
    <table className="message-table">
      <thead>
        <tr>
          <th>User</th>
          <th>Message</th>
          <th>Label</th>
          <th>AI Prediction</th>
          <th>Confidence</th>
          <th>Review Status</th>
          <th>Usage Count</th>
          <th>Timestamp</th>
          <th>Reviewer</th>
        </tr>
      </thead>
      <tbody>
        {messages.map((msg) => {
          const currentLabel = LABELS.find((l) => l.name === msg.label);

          return (
            <tr key={msg.id}>
              <td>{msg.username}</td>
              <td>{msg.text}</td>
              <td style={{ position: "relative" }}>
                {msg.label === null ? (
                  <div style={{ display: "flex", gap: "4px" }}>
                    {LABELS.map((label) => (
                      <button
                        key={label.name}
                        className="label-button"
                        style={{
                          backgroundColor: label.color,
                          color: label.name === "Safe" ? "#000" : "#fff",
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
                      className="label-button"
                      style={{
                        backgroundColor: currentLabel?.color || "#98ff98",
                        color: msg.label === "Safe" ? "#000" : "#fff",
                      }}
                      onClick={() => handleLabelClick(msg.id)}
                    >
                      {msg.label}
                    </button>

                    {openDropdownId === msg.id && (
                      <div className="label-dropdown">
                        {LABELS.map((label) => (
                          <div
                            key={label.name}
                            className="label-option"
                            style={{
                              backgroundColor: label.color,
                              color: label.name === "Safe" ? "#000" : "#fff",
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
              <td>{msg.ai_prediction || "-"}</td>
              <td>
                {msg.ai_confidence != null
                  ? (msg.ai_confidence * 100).toFixed(1) + "%"
                  : "-"}
              </td>
              <td>{msg.review_status}</td>
              <td>{msg.usage_count}</td>
              <td>{new Date(msg.timestamp_message).toLocaleString()}</td>
              <td>{msg.reviewed_by || "-"}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
