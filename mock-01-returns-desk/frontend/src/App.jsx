import { useState } from "react";
import ReturnsList from "./ReturnsList";
import { createReturn } from "./api";

export default function App() {
  const [agent, setAgent] = useState("priya");
  const [customer, setCustomer] = useState("");
  const [orderNumber, setOrderNumber] = useState("");
  const [message, setMessage] = useState("");

  async function handleCreate(event) {
    event.preventDefault();
    try {
      const created = await createReturn({ customer, order_number: orderNumber }, agent);
      setMessage(`Logged return #${created.id}`);
      setCustomer("");
      setOrderNumber("");
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <main>
      <h1>Returns Desk</h1>
      <label>
        Acting as
        <input value={agent} onChange={(e) => setAgent(e.target.value)} />
      </label>
      <form onSubmit={handleCreate}>
        <input placeholder="Customer" value={customer} onChange={(e) => setCustomer(e.target.value)} />
        <input
          placeholder="Order number"
          value={orderNumber}
          onChange={(e) => setOrderNumber(e.target.value)}
        />
        <button type="submit">Log return</button>
      </form>
      {message && <p>{message}</p>}
      <ReturnsList />
    </main>
  );
}
