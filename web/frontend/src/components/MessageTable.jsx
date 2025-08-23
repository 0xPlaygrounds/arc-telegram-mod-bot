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
    await updateLabel(msgId, label);
    setOpenDropdownId(null);
    refreshMessages(); // refresh data from backend
  };

  return (
    <table className="message-table">
      <thead>
        <tr>
          <th>User</th>
          <th>Message</th>
          <th>Label</th>
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
                  // Show all buttons if unlabeled
                  LABELS.map((label) => (
                    <button
                      key={label.name}
                      className="label-button"
                      style={{ 
                        backgroundColor: label.color,
                        color: label.name === "Safe" ? "#000" : "#fff"
                      }}
                      onClick={() => handleLabelSelect(msg.id, label.name)}
                    >
                      {label.name}
                    </button>
                  ))
                ) : (
                  // Show only current label and dropdown if clicked
                  <>
                    <button
                      className="label-button"
                      style={{ 
                        backgroundColor: currentLabel?.color || "#98ff98", 
                        color: msg.label === "Safe" ? "#000" : "#fff"
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
                              color: label.name === "Safe" ? "#000" : "#fff"
                            }}
                            onClick={() => handleLabelSelect(msg.id, label.name)}
                          >
                            {label.name}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
