import React, { useState, useEffect } from "react";
import { fetchMessages, updateBlocklistStatus } from "./api";
import MessageTable from "./components/MessageTable";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");

  const loadMessages = async () => {
    try {
      setRefreshing(true);

      // Update blocklist statuses
      await updateBlocklistStatus();

      // fetch the messages
      const data = await fetchMessages();
      setMessages(data.messages || []);

      // Convert timestamp to CST
      const now = new Date();
      const options = {
        timeZone: "America/Chicago",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      };
      setLastRefreshed(now.toLocaleTimeString("en-US", options));
    } catch (e) {
      console.warn("Could not fetch messages, keeping previous data.", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadMessages();
  }, []);

  if (loading && messages.length === 0) {
    return <div className="loader">Loading messages...</div>;
  }

  return (
    <div className="dashboard p-6 text-white">
      <h1 className="text-3xl font-bold mb-6" style={{ color: "#98ff98" }}>
        Arc Moderation Dashboard
      </h1>

      {/* Refresh status */}
      <div className="flex items-center gap-4 mb-6">
        {refreshing ? (
          <span className="flex items-center text-sm text-white bg-blue-600/20 px-4 py-2 rounded-md border border-blue-400 animate-pulse">
            🔄 Refreshing…
          </span>
        ) : (
          <span className="text-sm text-gray-700 bg-gray-200 px-4 py-2 rounded-md border border-gray-300 inline-block">
            Last refreshed at {lastRefreshed || "—"} CST
          </span>
        )}
      </div>

      {/* Message table */}
      <div className="mt-4">
        <MessageTable
          messages={messages}
          refreshMessages={loadMessages}
          searchTerm={searchTerm}
        />
      </div>

      {messages.length === 0 && !loading && (
        <div className="mt-6 text-gray-400">No messages available</div>
      )}
    </div>
  );
}
