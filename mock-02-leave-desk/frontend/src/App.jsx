import { useState } from "react";
import LeaveBoard from "./LeaveBoard";
import { requestLeave } from "./api";

export default function App() {
  const [user, setUser] = useState("dpatel");
  const [employeeId, setEmployeeId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [message, setMessage] = useState("");

  async function handleRequest(event) {
    event.preventDefault();
    try {
      const leave = await requestLeave(
        {
          employee_id: Number(employeeId),
          leave_type: "annual",
          start_date: startDate,
          end_date: endDate,
        },
        user
      );
      setMessage(`Requested ${leave.days} days`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <main>
      <h1>Leave Desk</h1>
      <label>
        Acting as
        <input value={user} onChange={(e) => setUser(e.target.value)} />
      </label>
      <form onSubmit={handleRequest}>
        <input placeholder="Employee id" value={employeeId} onChange={(e) => setEmployeeId(e.target.value)} />
        <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
        <button type="submit">Request leave</button>
      </form>
      {message && <p>{message}</p>}
      <LeaveBoard />
    </main>
  );
}
