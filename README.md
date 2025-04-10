# API de Busca no arXiv

Uma API simples para buscar artigos científicos no repositório arXiv.

## Configuração Local

1. Clone o repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Execute a aplicação:
   ```
   python app.py
   ```

Por padrão, a API estará disponível em: http://localhost:5000

## Deploy na Vercel

Este projeto está configurado para deploy na plataforma Vercel. Siga os passos abaixo:

1. Instale a CLI da Vercel (se ainda não tiver):
   ```
   npm install -g vercel
   ```

2. No diretório do projeto, faça login na sua conta Vercel:
   ```
   vercel login
   ```

3. Faça o deploy:
   ```
   vercel
   ```

4. Siga as instruções no terminal para concluir o deploy.

5. Para atualizar um deploy existente:
   ```
   vercel --prod
   ```

## Uso como MCP Server (Model Context Protocol)

Esta API também pode ser usada como um servidor MCP para integração com o Cursor e outras ferramentas compatíveis.

### Configuração no Cursor

Para usar esta API como um MCP Server no Cursor:

1. Na interface do Cursor, vá para configurações (Settings)
2. Encontre a seção "MCP Servers" ou "Integrations"
3. Adicione um novo servidor com a URL:
   ```
   https://arxiv-api-backend.vercel.app/mcp
   ```
   ou sua URL personalizada, caso esteja hospedando em outro local.

### Uso

Uma vez configurado, você pode fazer consultas diretamente no Cursor:

```
Buscar machine learning
```

ou

```
Pesquisar quantum computing
```

O servidor MCP processará sua consulta e retornará os resultados mais relevantes do arXiv.

## Endpoints

### Buscar Artigos

```
GET /api/search
```

#### Parâmetros

| Parâmetro   | Tipo    | Obrigatório | Descrição                                               | Padrão       |
|-------------|---------|-------------|--------------------------------------------------------|--------------|
| query       | string  | Sim         | Termo de busca                                          | -            |
| start       | integer | Não         | Índice inicial dos resultados                           | 0            |
| max_results | integer | Não         | Número máximo de resultados (limitado a 50)             | 10           |
| sort_by     | string  | Não         | Critério de ordenação (relevance, lastUpdatedDate, submittedDate) | relevance    |
| sort_order  | string  | Não         | Ordem da ordenação (ascending, descending)              | descending   |

#### Exemplos de Uso

Busca simples:
```
GET /api/search?query=machine+learning
```

Busca com parâmetros adicionais:
```
GET /api/search?query=ti:"deep learning" AND au:Goodfellow&start=0&max_results=20&sort_by=lastUpdatedDate&sort_order=descending
```

### MCP (Model Context Protocol)

```
POST /mcp
```

Endpoint compatível com o protocolo MCP para integração com o Cursor e outras ferramentas. Aceita requisições POST no formato JSON.

#### Tipos de Requisição

1. **Metadata**
   ```json
   {
     "type": "metadata"
   }
   ```

2. **Generate**
   ```json
   {
     "type": "generate",
     "input": "Buscar quantum computing"
   }
   ```

### Operadores de Busca

Você pode usar operadores como AND, OR e aspas para criar buscas mais precisas:

- Busca por título: `ti:"deep learning"`
- Busca por autor: `au:Goodfellow`
- Combinações: `ti:"neural networks" AND cat:cs.LG`

Para mais detalhes sobre os operadores de busca, consulte a [documentação oficial da API do arXiv](https://info.arxiv.org/help/api/user-manual.html).

## Exemplo de Resposta

```json
{
  "total_results": 10,
  "start_index": 0,
  "items_per_page": 10,
  "articles": [
    {
      "id": "2101.12345",
      "title": "Um estudo sobre aprendizado de máquina",
      "summary": "Este artigo apresenta...",
      "published": "2021-01-01T00:00:00Z",
      "updated": "2021-01-02T00:00:00Z",
      "authors": ["Silva, João", "Souza, Maria"],
      "categories": ["cs.LG", "cs.AI"],
      "link": "https://arxiv.org/abs/2101.12345",
      "pdf_url": "https://arxiv.org/pdf/2101.12345.pdf"
    },
    ...
  ]
}
```

## Tecnologias Utilizadas

- Flask: framework web
- Requests: para realizar chamadas HTTP
- Feedparser: para processar as respostas XML do arXiv
- Vercel: plataforma de hospedagem

## Limitações

Esta API é um wrapper simples para a API oficial do arXiv. Ela está sujeita às mesmas limitações e restrições da API original, como o limite de taxa de requisições. Para projetos em produção, considere implementar mecanismos de cache e limitação de taxa.

## Atualizações

- **10/04/2023**: Implementação do servidor MCP para integração com o Cursor
- **10/04/2023**: Adição de suporte a streaming SSE (Server-Sent Events)
- **10/04/2023**: Reinício do backend para correção de problemas 