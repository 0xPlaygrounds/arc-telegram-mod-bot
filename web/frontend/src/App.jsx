import React, { useState, useEffect } from 'react';
import { fetchMessages } from './api';
import MessageTable from './components/MessageTable';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadMessages = async () => {
    setLoading(true);
    try {
      const data = await fetchMessages();
      setMessages(data);
    } catch (e) {
      console.error('Error fetching messages', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMessages();
  }, []);

  if (loading) return <div className="loader">Loading messages...</div>;

  return (
    <div className="dashboard">
      <h1 style={{ color: "#98ff98" }}>Arc Moderation Dashboard</h1>
      <MessageTable messages={messages} refreshMessages={loadMessages} />
    </div>
  );
}
