# 🐾 Veterinary Assistant Agent

This is an **LLM-powered veterinary assistant** that can:
- ✅ Calculate feeding amounts for dogs based on breed, weight, and activity level.
- ✅ Perform veterinary-related calculations (nutrition, dosage approximations, etc.).
- ✅ Help with IT troubleshooting for common veterinary software/technologies.

It can run:
- As a standalone API (via FastAPI).
- As a **Custom GPT inside ChatGPT** (via Actions).

---

## 🚀 Deploy on Render

1. Push this repo to GitHub.
2. Go to [Render.com](https://render.com/) → New → Web Service.
3. Connect your GitHub repo.
4. Render will detect the `render.yaml` and auto-configure.
5. Add an environment variable in Render:
   - Key: `OPENAI_API_KEY`
   - Value: your OpenAI API key
6. Deploy 🎉

Your service will be live at:  
👉 `https://my-vet-agent.onrender.com`

---

## 📲 Install in ChatGPT

1. Open [ChatGPT](https://chat.openai.com/) → **Explore GPTs → Create**.
2. Under **Actions**, upload `backend/openapi.yaml`.
3. Set base URL = `https://my-vet-agent.onrender.com`
4. Save and share your GPT link ✅

---

## 🔧 Development

- Extend logic in `backend/app.py`.
- Update `backend/openapi.yaml` for new endpoints.
- Re-upload schema into ChatGPT when adding endpoints.
