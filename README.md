# Padaria dos Sonhos ERP

Sistema comercial para operação de padarias, desenvolvido por etapas.

## Fundação atual
- Login, cadastro, logout e sessão persistente
- Perfis Administrador, Caixa e Funcionário
- Dashboard com faturamento, lucro, despesas, vendas recentes e alertas
- Tema claro/escuro e layout responsivo

## Organização
- `backend/server.py`: API atual e autenticação
- `frontend/src/App.js`: experiência principal da fundação
- `docs/MER.md`: modelo entidade-relacionamento e decisões de dados
- `memory/ROADMAP.md`: evolução priorizada do produto

## Execução
O ambiente já inicia frontend e backend automaticamente. A API usa as variáveis protegidas existentes em `backend/.env`.
