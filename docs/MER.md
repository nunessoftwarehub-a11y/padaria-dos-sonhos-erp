# MER — Fundação do Padaria dos Sonhos ERP

## Entidades

```mermaid
erDiagram
  USER ||--o{ CASH_SESSION : opens
  USER ||--o{ SALE : registers
  USER }o--|| ROLE : has
  BAKERY ||--o{ USER : employs
  BAKERY ||--o{ INGREDIENT : owns
  BAKERY ||--o{ RECIPE : owns
  BAKERY ||--o{ PRODUCT : sells
  RECIPE ||--o{ RECIPE_INGREDIENT : contains
  INGREDIENT ||--o{ RECIPE_INGREDIENT : used_in
  RECIPE ||--o{ PRODUCTION : produces
  PRODUCT ||--o{ SALE_ITEM : sold_as
  SALE ||--o{ SALE_ITEM : contains
```

## Decisões
- Nesta primeira versão, o domínio começa com uma padaria; `BAKERY` já é reservado para a futura separação multiempresa.
- Usuários possuem um papel principal e a autorização será centralizada em middleware.
- Valores monetários serão armazenados em centavos e quantidades com precisão decimal no Prisma/PostgreSQL.
- Estoque será auditável através de movimentos, nunca alterado sem histórico.

## Próxima migração Prisma
As tabelas previstas são `Bakery`, `User`, `Role`, `Ingredient`, `Supplier`, `Recipe`, `RecipeIngredient`, `Product`, `Production`, `StockMovement`, `Sale`, `SaleItem`, `Payment`, `CashSession`, `Expense` e `Customer`.