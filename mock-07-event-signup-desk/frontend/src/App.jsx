import { useState } from "react";
import EventBoard from "./EventBoard.jsx";
import { createEvent } from "./api.js";

export default function App() {
  const [user, setUser] = useState("olivia");
  const [title, setTitle] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [capacity, setCapacity] = useState(20);
  const [message, setMessage] = useState("");

  async function submit(event) {
    event.preventDefault();
    try {
      const created = await createEvent(user, { title, startsAt, capacity: Number(capacity) });
      setMessage(`Created "${created.title}" as ${created.status}`);
      setTitle("");
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <main>
      <h1>Event sign-up desk</h1>
      <label>
        Signed in as <input value={user} onChange={(e) => setUser(e.target.value)} />
      </label>
      <form onSubmit={submit}>
        <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <input type="datetime-local" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} />
        <input
          type="number"
          min="1"
          max="500"
          value={capacity}
          onChange={(e) => setCapacity(e.target.value)}
        />
        <button type="submit">Create event</button>
      </form>
      {message && <p>{message}</p>}
      <EventBoard user={user} />
    </main>
  );
}
