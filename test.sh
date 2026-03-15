#!/bin/bash
curl -X POST http://localhost:8000/check-tab -H "Content-Type: application/json" -d '{"url": "https://mem0.ai", "title": "Mem0 - The Memory Layer for AI Apps"}'
