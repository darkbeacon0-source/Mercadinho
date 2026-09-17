# Mercadinho

Sistema web simples para controle de produtos, estoque, validade e vendas.

## Recursos
- Cadastro e edição de produtos
- Código de barras, categoria, fornecedor e preços
- Controle de quantidade e estoque mínimo
- Controle de validade
- Registro de vendas
- Baixa automática do estoque
- Histórico de vendas
- Dashboard com vendas do dia e alertas

## Como executar

1. Instale Python 3.11+.
2. No terminal, dentro da pasta do projeto:

```bash
python -m venv .venv
```

Windows:
```bash
.venv\\Scripts\\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Execute:

```bash
python app.py
```

5. Abra no navegador: http://127.0.0.1:5000

O banco SQLite `mercadinho.db` é criado automaticamente.
