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
            "search": "/api/search?query=TERMO_DE_BUSCA"
        }
    })

@app.route('/api/search', methods=['GET'])
def search():
    # Obter parâmetro de consulta
    query = request.args.get('query')
    
    # Validação básica
    if not query:
        return jsonify({"error": "O parâmetro 'query' é obrigatório"}), 400
    
    try:
        # Fazer a requisição para a API do arXiv
        url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": query,
            "start": 0,
            "max_results": 5  # Limitado a 5 para simplificar
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # Processar a resposta
        feed = feedparser.parse(response.text)
        
        # Extrair apenas informações básicas
        articles = []
        for entry in feed.entries:
            article = {
                "title": entry.title if "title" in entry else None,
                "summary": entry.summary if "summary" in entry else None,
                "authors": [author.name for author in entry.authors] if "authors" in entry else [],
                "link": entry.link if "link" in entry else None,
            }
            articles.append(article)
        
        return jsonify({
            "query": query,
            "articles": articles
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Erro ao acessar a API do arXiv: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro ao processar a resposta: {str(e)}"}), 500

if __name__ == '__main__':
    app.run() 