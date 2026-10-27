import { useState } from "react";
import LoanBoard from "./LoanBoard";
import { createLoan, extendLoan, returnLoan } from "./api";

export default function App() {
  const [user, setUser] = useState("clerk1");
  const [borrower, setBorrower] = useState("");
  const [start, setStart] = useState("");
  const [equipmentId, setEquipmentId] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [loanId, setLoanId] = useState("");
  const [returnedOn, setReturnedOn] = useState("");
  const [message, setMessage] = useState("");

  async function handleCreate(event) {
    event.preventDefault();
    try {
      const items = [{ equipment_id: Number(equipmentId), quantity: Number(quantity) }];
      const loan = await createLoan(borrower, start, items, user);
      setMessage(`Loan ${loan.id} is due ${loan.due_on}`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function handleReturn(event) {
    event.preventDefault();
    try {
      const loan = await returnLoan(loanId, returnedOn, user);
      setMessage(`Loan ${loan.id} returned, late fee ${(loan.fee_cents / 100).toFixed(2)}`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function handleExtend() {
    try {
      const loan = await extendLoan(loanId, 2, user);
      setMessage(`Loan ${loan.id} now due ${loan.due_on}`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <main>
      <h1>Equipment Loan Desk</h1>
      <label>
        Acting as
        <input value={user} onChange={(e) => setUser(e.target.value)} />
      </label>
      <form onSubmit={handleCreate}>
        <input placeholder="Borrower" value={borrower} onChange={(e) => setBorrower(e.target.value)} />
        <input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
        <input placeholder="Equipment id" value={equipmentId} onChange={(e) => setEquipmentId(e.target.value)} />
        <input type="number" min="1" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
        <button type="submit">Lend</button>
      </form>
      <form onSubmit={handleReturn}>
        <input placeholder="Loan id" value={loanId} onChange={(e) => setLoanId(e.target.value)} />
        <input type="date" value={returnedOn} onChange={(e) => setReturnedOn(e.target.value)} />
        <button type="submit">Return</button>
        <button type="button" onClick={handleExtend}>
          Extend 2 days
        </button>
      </form>
      {message && <p>{message}</p>}
      <LoanBoard />
    </main>
  );
}
