import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import "@/Module.css";
import CrudModule from "@/CrudModule";
import {
  BarChart3, Bell, ChevronDown, Coffee, CreditCard, LayoutDashboard,
  LogOut, Menu, Moon, Package, Search, Settings, Sun, UserCog, Users, WalletCards,
} from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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
  { id: "employees", label: "Funcionários", icon: UserCog },
  { id: "settings", label: "Configurações", icon: Settings },
];

const roleAccess = {
  cashier: ["overview", "pos", "products", "customers"],
  staff: ["overview", "pos", "products", "customers", "ingredients", "inventory", "recipes", "production"],
};

const money = (value) => `R$ ${Number(value || 0).toFixed(2).replace(".", ",")}`;
const shade = (hex, pct) => { const n = parseInt(hex.slice(1), 16); const f = (c) => Math.max(0, Math.min(255, Math.round(c * (1 + pct)))); const r = f(n >> 16), g = f((n >> 8) & 255), b = f(n & 255); return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`; };

function Overview({ onNewSale }) {
  const [data, setData] = useState(null);
  useEffect(() => { axios.get(`${API}/dashboard/summary`, { withCredentials: true }).then((response) => setData(response.data)).catch(() => {}); }, []);
  const cards = [
    { id: "day-total", label: "Faturamento diário", value: data ? money(data.day_total) : "—", hint: data ? `${data.day_sales_count} vendas hoje` : "Carregando..." },
    { id: "month-total", label: "Faturamento mensal", value: data ? money(data.month_total) : "—", hint: data ? `Lucro real do mês: ${money(data.real_month_profit)}` : "Acumulado do mês" },
    { id: "day-profit", label: "Lucro do dia", value: data ? money(data.day_profit) : "—", hint: "Receita menos custo dos itens" },
    { id: "day-expenses", label: "Despesas do dia", value: data ? money(data.day_expenses) : "—", hint: "Sangrias do caixa" },
  ];
  const maxDay = data?.last_7_days ? Math.max(...data.last_7_days.map((day) => day.total), 1) : 1;
  return <div className="module-content"><div className="module-heading"><div><p className="eyebrow">VISÃO GERAL</p><h1>Seu painel</h1><p className="subtle">Acompanhe o movimento real da sua padaria.</p></div><button data-testid="overview-new-sale-button" className="primary-button" onClick={onNewSale}><CreditCard size={16} /> Nova venda</button></div><section className="metric-grid">{cards.map((card) => <article data-testid={`metric-${card.id}`} className="metric-card" key={card.id}><div className="metric-top"><span>{card.label}</span></div><strong>{card.value}</strong><small>{card.hint}</small></article>)}</section>{data?.last_7_days && <section className="panel chart-panel" data-testid="overview-sales-chart"><p className="eyebrow">EVOLUÇÃO</p><h3>Faturamento — últimos 7 dias</h3><div className="bar-chart">{data.last_7_days.map((day) => <div className="bar-col" key={day.date}><span className="bar-value">{day.total > 0 ? money(day.total) : ""}</span><div className="bar" style={{ height: `${Math.max(4, day.total / maxDay * 130)}px` }} /><span className="bar-label">{new Date(day.date + "T12:00:00").toLocaleDateString("pt-BR", { weekday: "short" }).replace(".", "")}</span></div>)}</div></section>}<section className="dashboard-grid"><article className="panel"><p className="eyebrow">MOVIMENTO</p><h3>Vendas recentes</h3>{!data?.recent_sales?.length ? <p data-testid="overview-sales-empty" className="subtle">Nenhuma venda registrada ainda.</p> : <div className="record-list">{data.recent_sales.map((sale) => <div data-testid="overview-sale-row" className="record-row" key={sale.id}><strong>{sale.product_name}</strong><span>{sale.payment_method || "—"}</span><b>{money(sale.total)}</b></div>)}</div>}</article><article className="panel"><p className="eyebrow">ESTOQUE</p><h3>Estoque mínimo</h3>{!data?.low_stock?.length ? <p data-testid="overview-stock-empty" className="subtle">Nenhum alerta de estoque no momento.</p> : <div className="record-list">{data.low_stock.map((product) => <div data-testid="overview-stock-row" className="record-row" key={product.id}><strong>{product.name}</strong><span>restam {product.stock_quantity}</span></div>)}</div>}</article></section></div>;
}

export default function Dashboard({ user, onLogout }) {
  const [dark, setDark] = useState(false);
  const [page, setPage] = useState("overview");
  const [mobileMenu, setMobileMenu] = useState(false);
  const [posFull, setPosFull] = useState(false);
  const [settings, setSettings] = useState(null);
  const [logoUrl, setLogoUrl] = useState(null);
  const loadSettings = useCallback(() => {
    axios.get(`${API}/settings`, { withCredentials: true }).then(({ data }) => {
      setSettings(data);
      if (data.logo_path) axios.get(`${API}/settings/logo`, { withCredentials: true, responseType: "blob" }).then((response) => setLogoUrl((old) => { if (old) URL.revokeObjectURL(old); return URL.createObjectURL(response.data); })).catch(() => setLogoUrl(null));
      else setLogoUrl(null);
    }).catch(() => {});
  }, []);
  useEffect(() => { loadSettings(); }, [loadSettings]);
  useEffect(() => { if (settings?.primary_color) { const root = document.documentElement; root.style.setProperty("--amber", settings.primary_color); root.style.setProperty("--amber-dark", shade(settings.primary_color, -0.18)); } }, [settings]);
  const visibleMenu = user.role === "admin" ? menu : menu.filter((item) => (roleAccess[user.role] || roleAccess.cashier).includes(item.id));
  const logout = async () => { await axios.post(`${API}/auth/logout`, {}, { withCredentials: true }); onLogout(); };
  const current = visibleMenu.find((item) => item.id === page) || visibleMenu[0];
  const bakeryName = settings?.bakery_name || "Padaria dos Sonhos";
  const content = current.id === "overview" ? <Overview onNewSale={() => setPage("pos")} /> : current.id === "pos" ? <CrudModule type="pos" fullscreen={posFull} setFullscreen={setPosFull} /> : current.id === "products" ? <CrudModule type="products" /> : current.id === "ingredients" ? <CrudModule type="ingredients" /> : current.id === "customers" ? <CrudModule type="customers" /> : current.id === "recipes" ? <CrudModule type="recipes" /> : current.id === "production" ? <CrudModule type="production" /> : current.id === "finance" ? <CrudModule type="finance" /> : current.id === "reports" ? <CrudModule type="reports" /> : current.id === "employees" ? <CrudModule type="employees" /> : current.id === "settings" ? <CrudModule type="settings" onSettingsSaved={loadSettings} /> : <div className="module-content"><div className="module-heading"><div><p className="eyebrow">MÓDULO</p><h1>{current.label}</h1><p className="subtle">Esta área está pronta para receber os dados da sua operação.</p></div></div><section data-testid={`${current.id}-empty-state`} className="empty-state"><h2>Nenhum registro ainda</h2><p>Comece cadastrando os dados da sua padaria.</p></section></div>;
  const layoutClass = `${dark ? "app-layout dark-mode" : "app-layout"}${current.id === "pos" && posFull ? " pos-full" : ""}`;
  return <div className={layoutClass}><aside className={mobileMenu ? "sidebar open" : "sidebar"}><div className="sidebar-brand">{logoUrl ? <img data-testid="brand-logo" src={logoUrl} alt="Logo da padaria" className="brand-logo" /> : <span className="brand-mark"><Coffee size={18} /></span>}<span data-testid="brand-name">{bakeryName.toUpperCase()}</span></div><div className="workspace"><span className="workspace-avatar">{bakeryName.slice(0, 2).toUpperCase()}</span><span><b>{bakeryName}</b><small>Unidade principal</small></span><ChevronDown size={15} /></div><nav>{visibleMenu.map(({ id, label, icon: Icon }) => <button data-testid={`nav-${id}-button`} className={page === id ? "nav-item active" : "nav-item"} onClick={() => { setPage(id); setMobileMenu(false); }} key={id}><Icon size={18} /><span>{label}</span></button>)}</nav><div className="sidebar-bottom"><div className="user-chip"><span className="avatar">{user.name.slice(0, 2).toUpperCase()}</span><span><b>{user.name}</b><small>{user.role_label}</small></span></div><button data-testid="logout-button" className="logout-button" onClick={logout}><LogOut size={17} /></button></div></aside><main className="dashboard-main"><header className="topbar"><button data-testid="mobile-menu-button" className="icon-button mobile-only" onClick={() => setMobileMenu(!mobileMenu)}><Menu size={20} /></button><div className="breadcrumb"><span>Início</span><b>/</b><strong>{current.label}</strong></div><div className="topbar-actions"><button data-testid="search-button" className="icon-button"><Search size={18} /></button><button data-testid="notifications-button" className="icon-button notification"><Bell size={18} /><i /></button><button data-testid="theme-toggle-button" className="icon-button" onClick={() => setDark(!dark)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button></div></header>{content}</main></div>;
}
