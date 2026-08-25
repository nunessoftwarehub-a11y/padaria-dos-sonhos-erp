import { useEffect, useState } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import axios from "axios";
import "@/App.css";
import Login from "@/Login";
import Dashboard from "@/Dashboard";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    axios.get(`${API}/auth/me`, { withCredentials: true })
      .then(({ data }) => setUser(data)).catch(() => {}).finally(() => setChecking(false));
  }, []);
  if (checking) return <div data-testid="auth-loading" className="loading-screen">Preparando seu painel...</div>;
  return <BrowserRouter><Routes><Route path="*" element={user ? <Dashboard user={user} onLogout={() => setUser(null)} /> : <Login onLogin={setUser} />} /></Routes></BrowserRouter>;
}