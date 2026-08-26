import { useState } from "react";
import axios from "axios";
import "@/Module.css";
import CrudModule from "@/CrudModule";
import {
  BarChart3, Bell, ChevronDown, Coffee, CreditCard, LayoutDashboard,
  LogOut, Menu, Moon, Package, Search, Settings, Sun, Users, WalletCards,
} from "lucide-react";

const menu = [
  { id: "overview", label: "Visão geral", icon: LayoutDashboard },
  { id: "pos", label: "PDV", icon: CreditCard },
  { id: "products", label: "Produtos", icon: Package },
  { id: "ingredients", label: "Ingredientes", icon: Package },
  { id: "inventory", label: "Estoque", icon: Package },
  { id: "recipes", label: "Receitas", icon: Coffee },
  { id: "production", label: "Produção", icon: Coffee },
  { id: "finance", label: "Financeiro", icon: WalletCards },
  { id: "reports", label: "Relatórios", icon: BarChart3 },
  { id: "customers", label: "Clientes", icon: Users },
  { id: "settings", label: "Configurações", icon: Settings },
];


function Overview() {
  const cards = ["Faturamento diário", "Faturamento mensal", "Lucro", "Despesas"];
  return <div className="module-content"><div className="module-heading"><div><p className="eyebrow">VISÃO GERAL</p><h1>Seu painel</h1><p className="subtle">Os indicadores da sua operação aparecerão aqui.</p></div><button data-testid="overview-new-sale-button" className="primary-button"><CreditCard size={16} /> Nova venda</button></div><section className="metric-grid">{cards.map((label) => <article data-testid={`empty-metric-${label.toLowerCase().replaceAll(" ", "-")}`} className="metric-card empty-metric" key={label}><div className="metric-top"><span>{label}</span><span>—</span></div><strong>—</strong><small>Aguardando dados</small></article>)}</section><section className="dashboard-grid"><article data-testid="overview-sales-empty" className="panel empty-panel"><p className="eyebrow">MOVIMENTO</p><h3>Vendas recentes</h3><p>Nenhuma venda registrada.</p><button data-testid="overview-sales-action" className="link-button">Registrar primeira venda <span>→</span></button></article><article data-testid="overview-stock-empty" className="panel empty-panel"><p className="eyebrow">ESTOQUE</p><h3>Estoque mínimo</h3><p>Nenhum ingrediente cadastrado.</p><button data-testid="overview-stock-action" className="link-button">Adicionar ingrediente <span>→</span></button></article></section></div>;
}

export default function Dashboard({ user, onLogout }) {
  const [dark, setDark] = useState(false);
  const [page, setPage] = useState("overview");
  const [mobileMenu, setMobileMenu] = useState(false);
  const logout = async () => { await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/auth/logout`, {}, { withCredentials: true }); onLogout(); };
  const current = menu.find((item) => item.id === page);
  const content = page === "overview" ? <Overview /> : page === "pos" ? <CrudModule type="pos" /> : page === "products" ? <CrudModule type="products" /> : page === "ingredients" ? <CrudModule type="ingredients" /> : page === "customers" ? <CrudModule type="customers" /> : page === "recipes" ? <CrudModule type="recipes" /> : <div className="module-content"><div className="module-heading"><div><p className="eyebrow">MÓDULO</p><h1>{current.label}</h1><p className="subtle">Esta área está pronta para receber os dados da sua operação.</p></div></div><section data-testid={`${page}-empty-state`} className="empty-state"><h2>Nenhum registro ainda</h2><p>Comece cadastrando os dados da sua padaria.</p></section></div>;
  return <div className={dark ? "app-layout dark-mode" : "app-layout"}><aside className={mobileMenu ? "sidebar open" : "sidebar"}><div className="sidebar-brand"><span className="brand-mark"><Coffee size={18} /></span><span>PADARIA<br /><strong>DOS SONHOS</strong></span></div><div className="workspace"><span className="workspace-avatar">PS</span><span><b>Padaria dos Sonhos</b><small>Unidade principal</small></span><ChevronDown size={15} /></div><nav>{menu.map(({ id, label, icon: Icon }) => <button data-testid={`nav-${id}-button`} className={page === id ? "nav-item active" : "nav-item"} onClick={() => { setPage(id); setMobileMenu(false); }} key={id}><Icon size={18} /><span>{label}</span></button>)}</nav><div className="sidebar-bottom"><div className="user-chip"><span className="avatar">{user.name.slice(0, 2).toUpperCase()}</span><span><b>{user.name}</b><small>{user.role_label}</small></span></div><button data-testid="logout-button" className="logout-button" onClick={logout}><LogOut size={17} /></button></div></aside><main className="dashboard-main"><header className="topbar"><button data-testid="mobile-menu-button" className="icon-button mobile-only" onClick={() => setMobileMenu(!mobileMenu)}><Menu size={20} /></button><div className="breadcrumb"><span>Início</span><b>/</b><strong>{current.label}</strong></div><div className="topbar-actions"><button data-testid="search-button" className="icon-button"><Search size={18} /></button><button data-testid="notifications-button" className="icon-button notification"><Bell size={18} /><i /></button><button data-testid="theme-toggle-button" className="icon-button" onClick={() => setDark(!dark)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button></div></header>{content}</main></div>;
}