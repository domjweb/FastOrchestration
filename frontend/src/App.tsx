
import { useEffect, useState } from 'react';

type Request = {
  id: number;
  title: string;
  description?: string;
  type: string;
  priority: string;
  status: string;
  assignee_id?: number;
  created_at: string;
  updated_at: string;
};

type Event = {
  eventType: string;
  timestamp: string;
  requestId: number;
};

const API_URL = `${import.meta.env.VITE_API_URL}/api`;

function App() {
  const [requests, setRequests] = useState<Request[]>([]);
  const [events, setEvents] = useState<Event[]>([]);
  const [form, setForm] = useState({
    title: '',
    description: '',
    type: '',
    priority: '',
  });
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/requests`)
      .then((r) => r.json())
      .then(setRequests);
  }, []);

  useEffect(() => {
    if (selectedId) {
      fetch(`${API_URL}/requests/${selectedId}/events`)
        .then((r) => r.json())
        .then(setEvents);
    }
  }, [selectedId]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    const resp = await fetch(`${API_URL}/requests`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    });
    if (resp.ok) {
      const newReq = await resp.json();
      setRequests((prev) => [newReq, ...prev]);
      setForm({ title: '', description: '', type: '', priority: '' });
    }
    setLoading(false);
  }

  return (
    <div style={{ maxWidth: 900, margin: '2rem auto', fontFamily: 'system-ui' }}>
      <h1>Requests Hub</h1>
      <form onSubmit={handleSubmit} style={{ marginBottom: 24, background: '#f9f9f9', padding: 16, borderRadius: 8 }}>
        <h2>New Request</h2>
        <input name="title" placeholder="Title" value={form.title} onChange={handleChange} required style={{ marginRight: 8 }} />
        <input name="type" placeholder="Type" value={form.type} onChange={handleChange} required style={{ marginRight: 8 }} />
        <select name="priority" value={form.priority} onChange={handleChange} required style={{ marginRight: 8 }}>
          <option value="">Priority</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <textarea name="description" placeholder="Description" value={form.description} onChange={handleChange} style={{ marginRight: 8, verticalAlign: 'top' }} />
        <button type="submit" disabled={loading}>Create</button>
      </form>
      <h2>Requests</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 24 }}>
        <thead>
          <tr style={{ background: '#eee' }}>
            <th>ID</th>
            <th>Title</th>
            <th>Type</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Created</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {requests.map((r) => (
            <tr key={r.id} style={{ background: selectedId === r.id ? '#e0e7ff' : undefined }}>
              <td>{r.id}</td>
              <td>{r.title}</td>
              <td>{r.type}</td>
              <td>{r.priority}</td>
              <td>{r.status}</td>
              <td>{new Date(r.created_at).toLocaleString()}</td>
              <td>
                <button onClick={() => setSelectedId(r.id)}>Timeline</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {selectedId && (
        <div style={{ background: '#f3f4f6', padding: 16, borderRadius: 8 }}>
          <h3>Event Timeline for Request #{selectedId}</h3>
          <ul>
            {events.map((e, i) => (
              <li key={i}>
                <b>{e.eventType}</b> at {new Date(e.timestamp).toLocaleString()}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
