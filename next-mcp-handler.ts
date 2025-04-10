// AVISO: Este é um arquivo de exemplo para uso em projetos Next.js
// Para usá-lo, você precisa ter instalado:
// - next: npm install next
// - micro: npm install micro

// pages/api/mcp.ts
import type { NextApiRequest, NextApiResponse } from 'next';

export const config = {
  api: {
    bodyParser: false,
    externalResolver: true, // Ajuda com timeouts em ambientes serverless
  },
};

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  // Configurar cabeçalhos CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  // Lidar com requisições OPTIONS (CORS preflight)
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // Configurar cabeçalhos SSE
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no' // Impede o buffering do Nginx
  });

  // Enviar resposta inicial
  res.write(`data: ${JSON.stringify({
    type: 'generate_response',
    response: 'Conectando ao servidor...\n',
    done: false
  })}\n\n`);

  // Configurar intervalo para enviar mensagens
  const interval = setInterval(() => {
    const data = JSON.stringify({
      type: 'generate_response',
      response: `Dados atualizados em: ${new Date().toLocaleTimeString()}\n`,
      done: false
    });
    
    res.write(`data: ${data}\n\n`);
  }, 2000);

  // Configurar intervalo para heartbeat para manter a conexão viva
  const heartbeat = setInterval(() => {
    res.write(`: heartbeat\n\n`);
  }, 15000);

  // Limpar intervalos quando a conexão for fechada
  req.on('close', () => {
    clearInterval(interval);
    clearInterval(heartbeat);
    res.end();
  });
} 