# Ambiente de desenvolvimento

- Windows (PowerShell/VS Code)
- Python 3.10 ou superior
- MySQL 8.0.16 ou superior

Na raiz do repositório, instale as dependências e crie a configuração local:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r src/python/requirements.txt
Copy-Item .env.example .env
```

Crie `eventos_mvp` e o usuário de aplicação no MySQL, configure `.env` e inicialize o schema:

```powershell
python src/python/main.py init-db
```

O `.env` contém credenciais locais, está no `.gitignore` e nunca deve ser commitado. Consulte o `README.md` para SQL de criação do usuário, comandos do MVP e instruções de teste.

Os testes unitários não precisam de um servidor MySQL:

```powershell
python -m unittest discover -s tests/python -v
```