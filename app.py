from flask import Flask, jsonify

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

if __name__ == '__main__':
    app.run() 