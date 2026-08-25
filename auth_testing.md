# Teste de autenticação

1. `POST /api/auth/register` cria um usuário com papel Funcionário.
2. `POST /api/auth/login` retorna o usuário e define cookie httpOnly.
3. `GET /api/auth/me` valida a sessão existente.
4. `POST /api/auth/logout` remove a sessão.
5. `POST /api/auth/forgot-password` não revela se o e-mail existe.