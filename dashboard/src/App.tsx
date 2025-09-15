import { useState } from "react";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";

function App() {
  const [token, setToken] = useState(localStorage.getItem("auth_token"));

  return token ? <Dashboard token={token} /> : <Login onLogin={setToken} />;
}

export default App;
