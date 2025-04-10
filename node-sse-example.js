const express = require('express');
const app = express();
const PORT = 3000;

// Middleware para CORS
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  next();
});

// Endpoint principal
app.get('/', (req, res) => {
  res.send(`
    <html>
      <head>
        <title>SSE Test</title>
      </head>
      <body>
        <h1>Server-Sent Events Test</h1>
        <div id="messages"></div>
        
        <script>
          const eventSource = new EventSource('/sse');
          const messages = document.getElementById('messages');
          
          eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const newElement = document.createElement('div');
            newElement.textContent = \`Time: \${data.time}, Count: \${data.count}\`;
            messages.appendChild(newElement);
          };
          
          eventSource.onerror = function(error) {
            console.error('EventSource error:', error);
            eventSource.close();
          };
        </script>
      </body>
    </html>
  `);
});

// Endpoint SSE
app.get('/sse', (req, res) => {
  // Configurar headers para SSE
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive'
  });
  
  // Enviar um evento inicial
  res.write(`data: ${JSON.stringify({ time: new Date().toISOString(), count: 0 })}\n\n`);
  
  // Contador para os eventos
  let count = 1;
  
  // Função para enviar eventos a cada 2 segundos
  const intervalId = setInterval(() => {
    res.write(`data: ${JSON.stringify({ time: new Date().toTimeString().split(' ')[0], count })}\n\n`);
    count++;
  }, 2000);
  
  // Tratar quando o cliente fechar a conexão
  req.on('close', () => {
    console.log('Client closed connection');
    clearInterval(intervalId);
  });
});

// Endpoint MCP compatível com SSE
app.post('/mcp', express.json(), (req, res) => {
  // Verificar o tipo de requisição
  const requestType = req.body?.type;
  
  if (!requestType) {
    return res.status(400).json({ error: 'Campo "type" é obrigatório' });
  }
  
  // Tratar as requisições de metadados
  if (requestType === 'metadata') {
    return res.json({
      type: 'metadata_response',
      metadata: {
        name: 'Express SSE Example',
        description: 'Exemplo de SSE em Node.js com Express',
        version: '1.0.0',
        author: 'NodeJS Example',
        capabilities: {
          search: true,
          streaming: true
        }
      }
    });
  }
  
  // Tratar as requisições de geração com streaming
  if (requestType === 'generate') {
    const input = req.body.input || '';
    
    // Configurar headers para SSE
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    });
    
    // Enviar um evento inicial
    res.write(`data: ${JSON.stringify({
      type: 'generate_response',
      response: `Processando: "${input}"\n`,
      done: false
    })}\n\n`);
    
    // Contador para os eventos
    let count = 0;
    const messages = [
      "Conectando ao servidor...",
      "Buscando informações...",
      "Processando dados...",
      "Formatando resultados...",
      `Resultado para: "${input}"`
    ];
    
    // Função para enviar eventos com intervalos
    const intervalId = setInterval(() => {
      if (count < messages.length) {
        const isDone = count === messages.length - 1;
        
        res.write(`data: ${JSON.stringify({
          type: 'generate_response',
          response: messages[count] + "\n",
          done: isDone
        })}\n\n`);
        
        count++;
        
        // Se acabaram as mensagens, encerrar o intervalo
        if (isDone) {
          clearInterval(intervalId);
        }
      }
    }, 1000);
    
    // Tratar quando o cliente fechar a conexão
    req.on('close', () => {
      console.log('Client closed connection');
      clearInterval(intervalId);
    });
    
    return; // Não encerrar a resposta
  }
  
  // Tratar outros tipos não suportados
  res.status(400).json({
    type: 'error',
    error: `Tipo de requisição não suportado: ${requestType}`
  });
});

// Iniciar o servidor
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
  console.log(`SSE endpoint available at http://localhost:${PORT}/sse`);
  console.log(`MCP endpoint available at http://localhost:${PORT}/mcp`);
}); 