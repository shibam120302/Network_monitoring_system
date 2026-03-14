import React, { useState } from 'react';
import { chat } from '../api';

export default function Chat({ apiBase }) {
  const [message, setMessage] = useState('');
  const [reply, setReply] = useState('');
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!message.trim()) return;
    setLoading(true);
    setReply('');
    try {
      const res = await chat(message);
      setReply(res.reply);
    } catch (e) {
      setReply('Error: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    'Which nodes are failing?',
    'Why is node-17 down?',
    'Show incidents in the last 24 hours',
    'Which node has the highest latency?',
  ];

  return (
    <div>
      <h1 className="page-title">AI Chat Agent</h1>
      <div className="card">
        <p className="muted">Ask questions about network state, incidents, and nodes.</p>
        <div className="chat-suggestions">
          {suggestions.map((s) => (
            <button key={s} type="button" className="btn small" onClick={() => setMessage(s)}>{s}</button>
          ))}
        </div>
        <div className="chat-input">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            placeholder="Ask a question..."
            className="input"
          />
          <button className="btn primary" onClick={send} disabled={loading}>{loading ? '...' : 'Send'}</button>
        </div>
        {reply && (
          <div className="chat-reply">
            <h4>Reply</h4>
            <p>{reply}</p>
          </div>
        )}
      </div>
    </div>
  );
}
