import { useState } from "react";
import CountBoard from "./CountBoard";
import { createSession, recordCount } from "./api";

export default function App() {
  const [user, setUser] = useState("ivy");
  const [location, setLocation] = useState("");
  const [scheduledFor, setScheduledFor] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [sku, setSku] = useState("");
  const [counted, setCounted] = useState("");
  const [message, setMessage] = useState("");

  async function handleCreate(event) {
    event.preventDefault();
    try {
      const session = await createSession({ location, scheduled_for: scheduledFor }, user);
      setMessage(`Created session ${session.id} at ${session.location}`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function handleCount(event) {
    event.preventDefault();
    try {
      const line = await recordCount(sessionId, sku, Number(counted), user);
      setMessage(`${line.sku}: expected ${line.expected}, counted ${line.counted}, variance ${line.variance}`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <main>
      <h1>Stock Count Desk</h1>
      <label>
        Acting as
        <input value={user} onChange={(e) => setUser(e.target.value)} />
      </label>
      <form onSubmit={handleCreate}>
        <input placeholder="Location" value={location} onChange={(e) => setLocation(e.target.value)} />
        <input type="date" value={scheduledFor} onChange={(e) => setScheduledFor(e.target.value)} />
        <button type="submit">Schedule count</button>
      </form>
      <form onSubmit={handleCount}>
        <input placeholder="Session id" value={sessionId} onChange={(e) => setSessionId(e.target.value)} />
        <input placeholder="SKU" value={sku} onChange={(e) => setSku(e.target.value)} />
        <input placeholder="Counted" value={counted} onChange={(e) => setCounted(e.target.value)} />
        <button type="submit">Record count</button>
      </form>
      {message && <p>{message}</p>}
      <CountBoard />
    </main>
  );
}
