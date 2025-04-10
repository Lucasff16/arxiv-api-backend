from flask import Flask, jsonify, request
import requests
import feedparser

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "API de busca no arXiv",
        "status": "online"
    })

@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        "message": "API de busca no arXiv",
        "endpoints": {
            "search": "/api/search?query=TERMO_DE_BUSCA&start=0&max_results=10&sort_by=relevance&sort_order=descending"
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

if __name__ == '__main__':
    app.run() 