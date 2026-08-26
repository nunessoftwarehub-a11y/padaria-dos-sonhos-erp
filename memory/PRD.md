# PRD — Padaria dos Sonhos ERP

## Problema original
Construir um ERP profissional e comercializável para gestão de padarias, iniciado pela fundação com banco, MER, autenticação, usuários e permissões, evoluindo por módulos até PDV, estoque, produção, financeiro e relatórios.

## Personas
- Proprietário/Administrador: acompanha resultado, controla permissões e configura a operação.
- Caixa: realiza vendas, pagamentos e fechamento de caixa.
- Funcionário: consulta estoque, receitas e registra produção.

## Arquitetura e decisões
- Frontend React existente com React Router, React Query, Tailwind e componentes de interface; visual orgânico e profissional preparado para receber logo e cores finais.
- API executável atual usa FastAPI/MongoDB por ser o serviço disponibilizado no ambiente; o MER e `backend/prisma/schema.prisma` preservam a modelagem escolhida para a futura fundação Node/Express/Prisma/PostgreSQL.
- Sessões usam JWT em cookie httpOnly, expiração curta, recuperação sem enumeração de usuários e bloqueio após cinco falhas.
- O domínio já reserva `Bakery` para futura separação multiempresa, embora a primeira operação seja de uma padaria.

## Requisitos principais
- Login, cadastro, logout, sessão persistente e recuperação de senha.
- Papéis Administrador, Caixa e Funcionário.
- Dashboard com faturamento, lucro, despesas, vendas e alertas de estoque.
- Todas as telas iniciam sem registros ou valores demonstrativos, prontas para os dados reais da padaria.
- Navegação funcional para Visão geral, PDV, Estoque, Produção, Financeiro, Relatórios, Clientes e Configurações.
- Documentação viva em MER, roadmap e changelog.

## Implementado em 2026-03-08
- Fundação visual responsiva com tema claro/escuro.
- API de autenticação e dashboard protegida.
- Modelo Prisma relacional inicial e MER em Mermaid.
- Testes independentes cobriram desktop, mobile, sessão, lockout e recuperação real.
- Módulos vazios com estados iniciais e ações de cadastro foram adicionados em 2026-03-08.
- Em 2026-03-08, adicionados cadastros persistentes de produtos, ingredientes, clientes, receitas e vendas.
- PDV passou a usar formas de pagamento selecionáveis; produtos calculam custo unitário e sugestão de venda; receitas calculam custo total e por unidade.

## Backlog priorizado
### P0
- Migrar a API executável para Node/Express/Prisma/PostgreSQL quando o serviço PostgreSQL estiver disponível.
- Resolver o preflight CORS no proxy público para devolver origem explícita e credenciais.

### P1
- Ingredientes, fornecedores, estoque auditável e compras.
- Receitas com custo automático e produção com baixa de ingredientes.
- Produtos, PDV e caixa.

### P2
- Financeiro, relatórios exportáveis, clientes, funcionários, Cloudinary e configurações da empresa.

## Próximas tarefas
1. Migrar os endpoints de autenticação para os modelos Prisma.
2. Criar a primeira migração PostgreSQL a partir do schema.
3. Implementar ingredientes e movimentos de estoque.