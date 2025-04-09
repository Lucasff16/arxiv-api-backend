from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import feedparser
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/arxiv/search', methods=['GET'])
def search_arxiv():
    """
    Endpoint para buscar artigos no arXiv.
    
    Parâmetros de consulta:
    - query: termo de busca (obrigatório)
    - start: índice inicial dos resultados (padrão: 0)
    - max_results: número máximo de resultados (padrão: 10)
    - sort_by: critério de ordenação (padrão: 'relevance')
    - sort_order: ordem da ordenação (padrão: 'descending')
    
    Retorna:
    - JSON com os artigos encontrados
    """
    # Obter parâmetros da requisição
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
    if max_results > 100:
        max_results = 100
    
    # Construir a requisição para a API do arXiv
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order
    }
    
    try:
        # Fazer a requisição para a API do arXiv
        response = requests.get(url, params=params)
        response.raise_for_status()  # Lança exceção para códigos de erro HTTP
        
        # Processar a resposta XML usando feedparser
        feed = feedparser.parse(response.text)
        
        # Extrair informações relevantes dos artigos
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
            
            # Construir objeto do artigo
            article = {
                "id": entry.id.split("/")[-1] if "id" in entry else None,
                "title": entry.title.replace("\n", " ") if "title" in entry else None,
                "summary": entry.summary.replace("\n", " ") if "summary" in entry else None,
                "published": entry.published if "published" in entry else None,
                "updated": entry.updated if "updated" in entry else None,
                "authors": authors,
                "categories": categories,
                "link": entry.link if "link" in entry else None,
                "pdf_url": next((link.href for link in entry.links if link.rel == "alternate" and link.type == "application/pdf"), None) if "links" in entry else None
            }
            
            articles.append(article)
        
        # Construir a resposta
        result = {
            "total_results": int(feed.feed.opensearch_totalresults) if "opensearch_totalresults" in feed.feed else len(articles),
            "start_index": int(feed.feed.opensearch_startindex) if "opensearch_startindex" in feed.feed else start,
            "items_per_page": int(feed.feed.opensearch_itemsperpage) if "opensearch_itemsperpage" in feed.feed else len(articles),
            "articles": articles
        }
        
        return jsonify(result)
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Erro ao acessar a API do arXiv: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro ao processar a resposta: {str(e)}"}), 500

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        "message": "API de busca no arXiv",
        "endpoints": {
            "search": "/api/arxiv/search?query=TERMO_DE_BUSCA"
        },
        "documentation": "Consulte o README para mais detalhes"
    })

# Configure o modo de produção para o ambiente Vercel
app.config['ENV'] = 'production'
app.config['DEBUG'] = False

# O bloco abaixo só será executado quando rodarmos diretamente este arquivo
# Na Vercel, o arquivo index.py importa este módulo, então este bloco não será executado lá
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 