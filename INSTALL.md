# Installation Guide

## Run locally

1. Clone repo
   ```bash
   git clone https://github.com/YOUR-USERNAME/my-vet-agent.git
   cd my-vet-agent/backend
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Run
   ```bash
   uvicorn app:app --reload --port 8000
   ```

4. Open browser: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Deploy to Render

1. Push repo to GitHub.
2. On Render, create a new Web Service and link the repo.
3. Set `OPENAI_API_KEY` in Render dashboard → Environment Variables.
4. Deploy. Done ✅
