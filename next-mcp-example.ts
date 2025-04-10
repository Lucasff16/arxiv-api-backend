// AVISO: Este é um arquivo de exemplo para uso em projetos Next.js
// Para usá-lo, você precisa ter instalado:
// - next: npm install next
// - micro: npm install micro

// pages/api/mcp.ts
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

// Manipulador principal
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Configurar cabeçalhos CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  // Lidar com requisições OPTIONS
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Lidar com requisições GET (informações básicas)
  if (req.method === 'GET') {
    return res.json({
      message: "Endpoint MCP para integração com o Cursor",
      instructions: "Envie uma requisição POST com o campo 'type' definido como 'metadata' ou 'generate'"
    });
  }

  // Verificar se é uma requisição POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método não permitido' });
  }

  // Processar o corpo da requisição
  const body = await parseJsonBody(req);
  
  if (!body) {
    return res.status(400).json({ 
      type: 'error',
      error: 'Requisição sem dados JSON válidos' 
    });
  }

  // Verificar o tipo de requisição MCP
  const { type } = body;
  
  if (!type) {
    return res.status(400).json({ 
      type: 'error',
      error: 'Campo "type" não encontrado na requisição' 
    });
  }

  // Processar requisição de metadados
  if (type === 'metadata') {
    return res.json({
      type: 'metadata_response',
      metadata: {
        name: 'ArXiv Search (Next.js)',
        description: 'API para buscar artigos científicos no repositório arXiv',
        version: '1.0.0',
        author: 'Lucasff16',
        capabilities: {
          search: true,
          streaming: true
        }
      }
    });
  }

  // Processar requisição de geração
  if (type === 'generate') {
    // Obter input
    const { input } = body;
    
    if (!input) {
      return res.status(400).json({
        type: 'generate_response',
        response: 'Erro: Campo "input" não encontrado na requisição',
        done: true
      });
    }

    // Extrair a consulta
    let query = input;
    const prefixes = ["buscar ", "procurar ", "pesquisar ", "search "];
    if (prefixes.some(prefix => input.toLowerCase().startsWith(prefix))) {
      // Tentar extrair a consulta após o primeiro espaço
      const parts = input.split(" ", 2);
      if (parts.length > 1) {
        query = parts[1];
      }
    }

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
      response: `Buscando por '${query}' no arXiv...\n`,
      done: false
    })}\n\n`);

    // Simular busca no arXiv
    const mockResults = [
      {
        title: 'Exemplo de Artigo 1 sobre ' + query,
        authors: ['Autor A', 'Autor B'],
        categories: ['cs.AI', 'cs.LG'],
        link: 'https://arxiv.org/abs/0000.0000'
      },
      {
        title: 'Exemplo de Artigo 2 sobre ' + query,
        authors: ['Autor C', 'Autor D'],
        categories: ['cs.CL', 'cs.AI'],
        link: 'https://arxiv.org/abs/0000.0001'
      }
    ];

    // Enviar resultados com delay para simular processamento
    let count = 0;
    const interval = setInterval(() => {
      if (count < mockResults.length) {
        const result = mockResults[count];
        const isDone = count === mockResults.length - 1;
        
        // Formatar o resultado
        let resultText = `${count + 1}. ${result.title}\n`;
        resultText += `   Autores: ${result.authors.join(', ')}\n`;
        resultText += `   Categorias: ${result.categories.join(', ')}\n`;
        resultText += `   Link: ${result.link}\n\n`;
        
        // Enviar resultado
        res.write(`data: ${JSON.stringify({
          type: 'generate_response',
          response: resultText,
          done: isDone
        })}\n\n`);
        
        count++;
        
        // Se for o último resultado, limpar o intervalo
        if (isDone) {
          clearInterval(interval);
        }
      }
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

  // Lidar com outros tipos não suportados
  return res.status(400).json({
    type: 'error',
    error: `Tipo de requisição MCP não suportado: ${type}`
  });
} 