# Developer Guide

## Extending Agent Functionality

- Add new veterinary endpoints in `backend/app.py` (e.g., `/calculate_dose`, `/nutrition_plan`).
- Update `backend/openapi.yaml` to describe new endpoints.
- Re-upload schema into your Custom GPT.

## Deployment

- Locally: `uvicorn app:app --reload --port 8000`
- Render: Push changes → Redeploy automatically.
