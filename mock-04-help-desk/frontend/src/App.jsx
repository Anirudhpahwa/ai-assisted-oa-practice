import { useState } from "react";
import TicketBoard from "./TicketBoard";
import { addComment, createTicket } from "./api";

export default function App() {
  const [user, setUser] = useState("alice");
  const [title, setTitle] = useState("");
  const [requester, setRequester] = useState("");
  const [priority, setPriority] = useState("normal");
  const [ticketId, setTicketId] = useState("");
  const [body, setBody] = useState("");
  const [message, setMessage] = useState("");

  async function handleCreate(event) {
    event.preventDefault();
    try {
      const key = `${user}-${title}-${requester}`;
      const ticket = await createTicket({ title, requester, priority }, user, key);
      setMessage(`Ticket ${ticket.id} is due ${ticket.due_at}`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function handleComment(event) {
    event.preventDefault();
    try {
      const comment = await addComment(ticketId, body, false, user);
      setMessage(`Comment ${comment.id} added`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <main>
      <h1>Help Desk</h1>
      <label>
        Acting as
        <input value={user} onChange={(e) => setUser(e.target.value)} />
      </label>
      <form onSubmit={handleCreate}>
        <input placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <input placeholder="Requester" value={requester} onChange={(e) => setRequester(e.target.value)} />
        <select value={priority} onChange={(e) => setPriority(e.target.value)}>
          {["low", "normal", "high", "urgent"].map((name) => (
            <option key={name}>{name}</option>
          ))}
        </select>
        <button type="submit">Create ticket</button>
      </form>
      <form onSubmit={handleComment}>
        <input placeholder="Ticket id" value={ticketId} onChange={(e) => setTicketId(e.target.value)} />
        <input placeholder="Comment" value={body} onChange={(e) => setBody(e.target.value)} />
        <button type="submit">Add comment</button>
      </form>
      {message && <p>{message}</p>}
      <TicketBoard />
    </main>
  );
}
