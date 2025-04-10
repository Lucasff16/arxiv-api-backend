from flask import Flask, jsonify, request, Response, make_response, stream_with_context
import requests
import feedparser
import json
import time

app = Flask(__name__)

# Configuração CORS global
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

# Rota específica para CORS preflight
@app.route('/mcp', methods=['OPTIONS'])
def handle_preflight():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, Accept")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    response.headers.add("Access-Control-Max-Age", "3600")
    return response

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "API de busca no arXiv - MCP Server",
        "status": "online"
    })

@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        "message": "API de busca no arXiv",
        "endpoints": {
            "search": "/api/search?query=TERMO_DE_BUSCA&start=0&max_results=10&sort_by=relevance&sort_order=descending",
            "mcp": "/mcp - Endpoint para protocolo MCP do Cursor"
        }
    })

@app.route('/api/search', methods=['GET'])
def search():
    # Obter parâmetros de consulta
    query = request.args.get('query')
    start = request.args.get('start', 0)
    max_results = request.args.get('max_results', 10)
    sort_by = request.args.get('sort_by', 'relevance')
    sort_order = request.args.get('sort_order', 'descending')
    
    # Validação básica
    if not query:
        return jsonify({"error": "O parâmetro 'query' é obrigatório"}), 400
    
    try:
        start = int(start)
        max_results = int(max_results)
    except ValueError:
        return jsonify({"error": "Os parâmetros 'start' e 'max_results' devem ser números inteiros"}), 400
    
    # Limitar o número máximo de resultados para evitar sobrecarga
    if max_results > 50:
        max_results = 50
    
    try:
        # Fazer a requisição para a API do arXiv
        url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Processar a resposta
        feed = feedparser.parse(response.text)
        
        # Extrair informações dos artigos
        articles = []
        for entry in feed.entries:
            # Processar autores
            authors = []
            if 'authors' in entry:
                for author in entry.authors:
                    if 'name' in author:
                        authors.append(author.name)
            
            # Processar categorias
            categories = []
            if 'tags' in entry:
                for tag in entry.tags:
                    if 'term' in tag:
                        categories.append(tag.term)
            
            # Extrair ID do arXiv
            arxiv_id = entry.id.split("/")[-1] if "id" in entry else None
            
            # Extrair link para PDF
            pdf_url = None
            if "links" in entry:
                for link in entry.links:
                    if link.rel == "alternate" and link.type == "application/pdf":
                        pdf_url = link.href
                        break
            
            article = {
                "id": arxiv_id,
                "title": entry.title.replace("\n", " ") if "title" in entry else None,
                "summary": entry.summary.replace("\n", " ") if "summary" in entry else None,
                "published": entry.published if "published" in entry else None,
                "updated": entry.updated if "updated" in entry else None,
                "authors": authors,
                "categories": categories,
                "link": entry.link if "link" in entry else None,
                "pdf_url": pdf_url
            }
            
            articles.append(article)
        
        # Extrair informações de paginação
        total_results = int(feed.feed.opensearch_totalresults) if "opensearch_totalresults" in feed.feed else len(articles)
        start_index = int(feed.feed.opensearch_startindex) if "opensearch_startindex" in feed.feed else start
        items_per_page = int(feed.feed.opensearch_itemsperpage) if "opensearch_itemsperpage" in feed.feed else len(articles)
        
        return jsonify({
            "query": query,
            "total_results": total_results,
            "start_index": start_index,
            "items_per_page": items_per_page,
            "articles": articles
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Erro ao acessar a API do arXiv: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro ao processar a resposta: {str(e)}"}), 500

# Endpoint MCP unificado
@app.route('/mcp', methods=['GET', 'POST'])
def mcp_handler():
    """Endpoint principal para o protocolo MCP."""
    try:
        # Para requisições GET, retornar informações básicas
        if request.method == 'GET':
            return jsonify({
                "message": "Endpoint MCP para integração com o Cursor",
                "instructions": "Envie uma requisição POST com o campo 'type' definido como 'metadata' ou 'generate'"
            })
        
        # Para requisições POST
        request_data = request.json
        
        # Verificar se há dados JSON na requisição
        if not request_data:
            return jsonify({
                "type": "error",
                "error": "Requisição sem dados JSON válidos"
            }), 400
        
        # Verificar se o tipo está presente
        if 'type' not in request_data:
            return jsonify({
                "type": "error", 
                "error": "Campo 'type' não encontrado na requisição"
            }), 400
        
        # Processar de acordo com o tipo
        if request_data['type'] == 'metadata':
            return handle_metadata()
        elif request_data['type'] == 'generate':
            stream = request_data.get('stream', True)  # Por padrão, usamos streaming
            if stream:
                return handle_generate_stream(request_data)
            else:
                return handle_generate(request_data)
        else:
            return jsonify({
                "type": "error",
                "error": f"Tipo de requisição MCP não suportado: {request_data['type']}"
            }), 400
            
    except Exception as e:
        return jsonify({
            "type": "error",
            "error": f"Erro ao processar a requisição MCP: {str(e)}"
        }), 500

def handle_metadata():
    """Fornece metadados sobre o servidor MCP."""
    metadata = {
        "type": "metadata_response",
        "metadata": {
            "name": "ArXiv Search",
            "description": "API para buscar artigos científicos no repositório arXiv",
            "version": "1.0.0",
            "author": "Lucasff16",
            "capabilities": {
                "search": True,
                "streaming": True  # Atualizado para indicar que suportamos streaming
            }
        }
    }
    return jsonify(metadata)

def format_sse(data, event=None):
    """Formata uma mensagem SSE."""
    msg = f"data: {json.dumps(data)}\n\n"
    if event is not None:
        msg = f"event: {event}\n{msg}"
    return msg

def handle_generate_stream(request_data):
    """Processa uma requisição de geração com streaming no formato MCP."""
    def generate():
        if 'input' not in request_data:
            yield format_sse({
                "type": "generate_response",
                "response": "Erro: Campo 'input' não encontrado na requisição",
                "done": True
            })
            return
        
        input_text = request_data.get('input', '')
        
        # Extrair a consulta do texto de entrada
        # Se o texto começa com "buscar" ou "procurar", extrair a consulta
        query = None
        if input_text.lower().startswith(("buscar ", "procurar ", "pesquisar ", "search ")):
            query = input_text.split(" ", 1)[1]
        else:
            # Caso contrário, usar o texto completo como consulta
            query = input_text
        
        # Yield inicial indicando que iniciamos a busca
        yield format_sse({
            "type": "generate_response",
            "response": f"Buscando por '{query}' no arXiv...\n",
            "done": False
        })
        
        # Pequeno delay para simular processamento
        time.sleep(0.5)
        
        try:
            url = "https://export.arxiv.org/api/query"
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": 5
            }
            
            # Yield indicando que estamos fazendo a requisição
            yield format_sse({
                "type": "generate_response",
                "response": "Conectando ao arXiv...\n",
                "done": False
            })
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Yield indicando que estamos processando os resultados
            yield format_sse({
                "type": "generate_response",
                "response": "Processando resultados...\n",
                "done": False
            })
            
            # Pequeno delay para simular processamento
            time.sleep(0.5)
            
            feed = feedparser.parse(response.text)
            
            # Yield cabeçalho dos resultados
            yield format_sse({
                "type": "generate_response",
                "response": f"\nResultados da busca por '{query}' no arXiv:\n\n",
                "done": False
            })
            
            # Verificar se temos resultados
            if len(feed.entries) == 0:
                yield format_sse({
                    "type": "generate_response",
                    "response": "Nenhum resultado encontrado.",
                    "done": True
                })
                return
            
            # Enviar resultados um por um para simular streaming
            for i, entry in enumerate(feed.entries, 1):
                # Pequeno delay entre os resultados para simular streaming
                time.sleep(0.3)
                
                title = entry.title.replace("\n", " ") if "title" in entry else "Sem título"
                
                # Processar autores
                authors = []
                if 'authors' in entry:
                    for author in entry.authors:
                        if 'name' in author:
                            authors.append(author.name)
                authors_text = ", ".join(authors) if authors else "Autores não disponíveis"
                
                # Obter link
                link = entry.link if "link" in entry else None
                
                # Extrair categorias
                categories = []
                if 'tags' in entry:
                    for tag in entry.tags:
                        if 'term' in tag:
                            categories.append(tag.term)
                categories_text = ", ".join(categories) if categories else "Categorias não disponíveis"
                
                # Formatar o resultado atual
                result_text = f"{i}. {title}\n"
                result_text += f"   Autores: {authors_text}\n"
                result_text += f"   Categorias: {categories_text}\n"
                result_text += f"   Link: {link}\n\n"
                
                # Enviar parte atual do resultado
                done = (i == len(feed.entries))  # Último resultado?
                yield format_sse({
                    "type": "generate_response",
                    "response": result_text,
                    "done": done
                })
            
        except Exception as e:
            yield format_sse({
                "type": "generate_response",
                "response": f"Erro ao buscar no arXiv: {str(e)}",
                "done": True
            })
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Content-Type': 'text/event-stream',
            'Access-Control-Allow-Origin': '*'
        }
    )

def handle_generate(request_data):
    """Processa uma requisição de geração no formato MCP sem streaming."""
    if 'input' not in request_data:
        return jsonify({
            "type": "generate_response",
            "response": "Erro: Campo 'input' não encontrado na requisição",
            "done": True
        })
    
    input_text = request_data.get('input', '')
    
    # Extrair a consulta do texto de entrada
    # Se o texto começa com "buscar" ou "procurar", extrair a consulta
    query = None
    if input_text.lower().startswith(("buscar ", "procurar ", "pesquisar ", "search ")):
        query = input_text.split(" ", 1)[1]
    else:
        # Caso contrário, usar o texto completo como consulta
        query = input_text
    
    # Buscar no arXiv
    try:
        url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": 5
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        feed = feedparser.parse(response.text)
        
        # Formatar resultados em texto
        results_text = f"Resultados da busca por '{query}' no arXiv:\n\n"
        
        if len(feed.entries) == 0:
            results_text += "Nenhum resultado encontrado."
        else:
            for i, entry in enumerate(feed.entries, 1):
                title = entry.title.replace("\n", " ") if "title" in entry else "Sem título"
                
                # Processar autores
                authors = []
                if 'authors' in entry:
                    for author in entry.authors:
                        if 'name' in author:
                            authors.append(author.name)
                authors_text = ", ".join(authors) if authors else "Autores não disponíveis"
                
                # Obter link
                link = entry.link if "link" in entry else None
                
                # Extrair categorias
                categories = []
                if 'tags' in entry:
                    for tag in entry.tags:
                        if 'term' in tag:
                            categories.append(tag.term)
                categories_text = ", ".join(categories) if categories else "Categorias não disponíveis"
                
                results_text += f"{i}. {title}\n"
                results_text += f"   Autores: {authors_text}\n"
                results_text += f"   Categorias: {categories_text}\n"
                results_text += f"   Link: {link}\n\n"
        
        # Montar resposta no formato MCP
        return jsonify({
            "type": "generate_response",
            "response": results_text,
            "done": True
        })
        
    except Exception as e:
        return jsonify({
            "type": "generate_response",
            "response": f"Erro ao buscar no arXiv: {str(e)}",
            "done": True
        })

if __name__ == '__main__':
    app.run(debug=True) 