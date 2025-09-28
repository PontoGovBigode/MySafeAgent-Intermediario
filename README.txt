# MySafeAgent Intermediary Server

Este backend Flask permite:
- Registrar um QR Code (gerado pelo agente .exe)
- Autorizar o QR Code após escaneado pelo .apk
- Verificar o status de autorização remotamente

## Subir no Railway:
1. Crie conta em https://railway.app
2. Clique em "New Project" > "Deploy from GitHub" ou "Deploy from Template"
3. Suba os arquivos: server.py, requirements.txt, Procfile
4. Railway gerará um link como: https://mysafeagent.up.railway.app

Use este link na comunicação entre `.exe` e `.apk`.
