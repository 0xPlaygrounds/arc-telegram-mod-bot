import React, { useState, useEffect } from 'react';
import { fetchMessages } from './api';
import MessageTable from './components/MessageTable';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadMessages = async () => {
    try {
      const data = await fetchMessages();
      setMessages(data); // only update on successful fetch
    } catch (e) {
      console.warn('Could not fetch messages, keeping previous data.', e);
      // messages state remains unchanged
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load messages immediately on mount
    loadMessages();

    // Set up auto-refresh every 60 seconds
    const interval = setInterval(() => {
      loadMessages();
    }, 60000); // 1 minute

    // Cleanup interval on unmount
    return () => clearInterval(interval);
  }, []);

  if (loading && messages.length === 0) {
    return <div className="loader">Loading messages...</div>;
  }

  return (
    <div className="dashboard">
      <h1 style={{ color: "#98ff98" }}>Arc Moderation Dashboard</h1>
      <MessageTable messages={messages} refreshMessages={loadMessages} />
      {messages.length === 0 && !loading && (
        <div>No messages available</div>
      )}
    </div>
  );
}
