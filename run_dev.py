#!/usr/bin/env python3
"""
Development server with HTTPS support.

Run with (since we have local ssl certificates now):
python run_dev.py

Instead of:
uvicorn app.main:app --relaod

Or manually:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
  --ssl-keyfile=../mgl-frontend/certs/key.pem \
  --ssl-certfile=../mgl-frontend/certs/cert.pem
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile="../mgl-frontend/certs/key.pem",
        ssl_certfile="../mgl-frontend/certs/cert.pem",
    )