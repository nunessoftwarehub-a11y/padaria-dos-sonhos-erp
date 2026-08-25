import { useState } from "react";
import axios from "axios";
import { Coffee } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Login({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const submit = async (event) => {
    event.preventDefault(); setLoading(true); setError("");
    try { const { data } = await axios.post(`${API}/auth/${mode === "login" ? "login" : "register"}`, form, { withCredentials: true }); onLogin(data); }
    catch (e) { setError(typeof e.response?.data?.detail === "string" ? e.response.data.detail : "Não foi possível entrar agora."); }
    finally { setLoading(false); }
  };
  const recover = async () => {
    setLoading(true); setError("");
    try { await axios.post(`${API}/auth/forgot-password`, { email: form.email }, { withCredentials: true }); setError("Se o e-mail existir, enviaremos as instruções de recuperação."); }
    catch (e) { setError(typeof e.response?.data?.detail === "string" ? e.response.data.detail : "Informe um e-mail válido para continuar."); }
    finally { setLoading(false); }
  };
  return <main className="auth-shell"><section className="auth-visual"><div className="visual-top"><span className="brand-mark"><Coffee size={19} /></span><span>PADARIA DOS SONHOS</span></div><div className="visual-copy"><p className="eyebrow">OPERAÇÃO COM MAIS PROPÓSITO</p><h1>O sabor de uma padaria bem cuidada.</h1><p>Controle cada detalhe da sua produção, do primeiro ingrediente à última venda.</p></div><div className="visual-foot"><span>Fundação 01</span><span>ERP para quem faz acontecer</span></div></section><section className="auth-panel"><div className="auth-form-wrap"><div className="mobile-brand"><span className="brand-mark"><Coffee size={17} /></span><span>PADARIA DOS SONHOS</span></div><p className="eyebrow">BEM-VINDO DE VOLTA</p><h2>{mode === "login" ? "Acesse seu painel" : "Crie seu acesso"}</h2><p className="auth-subtitle">{mode === "login" ? "Tenha a operação da sua padaria na palma da mão." : "Comece a organizar sua padaria com clareza."}</p><form onSubmit={submit}>{mode === "register" && <label>Seu nome<input data-testid="register-name-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Como podemos chamar você?" /></label>}<label>E-mail<input data-testid="auth-email-input" type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} placeholder="voce@padaria.com" /></label><label>Senha<input data-testid="auth-password-input" type="password" required value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Mínimo de 6 caracteres" /></label>{error && <div data-testid="auth-error" className="auth-error">{error}</div>}<button data-testid="auth-submit-button" className="primary-button" disabled={loading}>{loading ? "Aguarde..." : mode === "login" ? "Entrar no painel" : "Criar meu acesso"}</button></form><button data-testid="auth-mode-toggle" className="text-button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>{mode === "login" ? "Ainda não tenho acesso" : "Já tenho uma conta"}</button>{mode === "login" && <button data-testid="forgot-password-button" className="forgot-button" onClick={recover} disabled={loading}>Esqueci minha senha</button>}</div><p className="auth-legal">Acesso protegido por sessão segura. Ao continuar, você concorda com os termos de uso.</p></section></main>;
}