# controle-financeiro
Aplicativo para controle das finanças pessoais

## Estilos (Tailwind CSS)

O CSS do app é gerado localmente em `css/tailwind.css` (sem CDN). Sempre que adicionar
ou alterar classes no `index.html` ou em `js/`, gere o CSS novamente e inclua o arquivo no commit:

```bash
python build_css.py          # gera css/tailwind.css (minificado)
python build_css.py --watch  # regera automaticamente durante o desenvolvimento
```

Na primeira execução o script baixa o Tailwind CSS Standalone CLI para `tools/`.
As cores e a fonte do tema ficam em `tailwind.config.js`.
