from app import app

# O Vercel espera uma variável chamada 'app' para servir a aplicação Flask
# Não é necessário chamar app.run() aqui, a Vercel fará isso

# Verificação para debug
if __name__ == "__main__":
    app.run() 