# Integração MCP com Next.js

Este documento descreve como implementar o protocolo MCP (Model Context Protocol) em uma aplicação Next.js para integração com o Cursor e outras ferramentas compatíveis.

## Requisitos

- Next.js 12 ou superior
- Pacote `micro` para parse de body (se estiver desativando o bodyParser padrão)

```bash
npm install micro
```

## Implementação

Para implementar um endpoint MCP em Next.js, você precisa criar um arquivo na pasta `pages/api/`. O exemplo a seguir mostra como criar um endpoint em `/api/mcp` que suporta Server-Sent Events (SSE).

### 1. Configuração Básica

Crie o arquivo `pages/api/mcp.ts` com a seguinte estrutura:

```typescript
import type { NextApiRequest, NextApiResponse } from 'next';
import { IncomingMessage } from 'http';
import { buffer } from 'micro';

// Desativar o bodyParser padrão
export const config = {
  api: {
    bodyParser: false,
    externalResolver: true,
  },
};

// Função auxiliar para processar o corpo da requisição
async function parseJsonBody(req: IncomingMessage) {
  try {
    const buf = await buffer(req);
    const body = JSON.parse(buf.toString());
    return body;
  } catch (e) {
    return null;
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Implementação do handler aqui
}
```

### 2. Configurando CORS

Adicione suporte a CORS para permitir que o Cursor acesse seu endpoint:

```typescript
// Dentro do handler
// Configurar cabeçalhos CORS
res.setHeader('Access-Control-Allow-Origin', '*');
res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

// Lidar com requisições OPTIONS
if (req.method === 'OPTIONS') {
  res.status(200).end();
  return;
}
```

### 3. Implementando Metadados

O endpoint MCP deve suportar requisições de metadados:

```typescript
// Verificar o tipo de requisição MCP
if (type === 'metadata') {
  return res.json({
    type: 'metadata_response',
    metadata: {
      name: 'Seu Serviço MCP',
      description: 'Descrição do seu serviço',
      version: '1.0.0',
      author: 'Seu Nome',
      capabilities: {
        search: true,
        streaming: true
      }
    }
  });
}
```

### 4. Implementando Server-Sent Events (SSE)

Para o tipo 'generate', você precisa configurar Server-Sent Events:

```typescript
if (type === 'generate') {
  // Obter input
  const { input } = body;
  
  // Configurar cabeçalhos SSE
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no'
  });

  // Enviar mensagem inicial
  res.write(`data: ${JSON.stringify({
    type: 'generate_response',
    response: 'Processando...\n',
    done: false
  })}\n\n`);

  // Simular processamento
  const interval = setInterval(() => {
    // Lógica de processamento
    
    // Enviar resultados
    res.write(`data: ${JSON.stringify({
      type: 'generate_response',
      response: 'Resultado...\n',
      done: true // true quando for o último resultado
    })}\n\n`);
    
    clearInterval(interval);
  }, 1000);
  
  // Heartbeat para manter a conexão viva
  const heartbeat = setInterval(() => {
    res.write(`: heartbeat\n\n`);
  }, 15000);
  
  // Limpar quando a conexão for fechada
  req.on('close', () => {
    clearInterval(interval);
    clearInterval(heartbeat);
    res.end();
  });
  
  return; // Não encerrar a resposta
}
```

## Vercel e Ambiente Serverless

O SSE pode ser desafiador em ambientes serverless como a Vercel devido aos timeouts. Aqui estão algumas dicas:

1. Use o flag `externalResolver: true` na configuração da API
2. Adicione heartbeats regulares para manter a conexão viva
3. Considere alternativas como WebSockets para projetos de produção que exigem conexões muito longas

## Configuração no Cursor

Para usar seu servidor MCP no Cursor, adicione-o às configurações do Cursor:

```json
{
  "mcpServers": {
    "seu-servidor": {
      "url": "https://seu-dominio.vercel.app/api/mcp",
      "enabled": true
    }
  }
}
```

## Exemplo Completo

Veja os arquivos `next-mcp-handler.ts` e `next-mcp-example.ts` neste repositório para exemplos completos de implementação.

## Limitações

- O ambiente serverless da Vercel tem um timeout máximo de 60 segundos para funções
- Para respostas muito longas, considere dividir o processamento em chunks menores
- Use heartbeats para manter a conexão viva 