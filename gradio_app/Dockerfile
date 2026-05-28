# Build context must be the project root so both lambdas/ and gradio_app/ are accessible.
# docker build -f gradio_app/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

# Install Python dependencies:
#   - Lambda agent deps (langchain, langgraph, langchain-openai)
#   - Gradio-specific deps (gradio, boto3)
COPY lambdas/music_store_agents/requirements.txt /tmp/lambda-requirements.txt
COPY gradio_app/requirements.txt /tmp/gradio-requirements.txt
RUN pip install --no-cache-dir \
        -r /tmp/lambda-requirements.txt \
        -r /tmp/gradio-requirements.txt

# Copy agent source (excluding .venv, tests, layers)
COPY lambdas/music_store_agents/graph.py            agents/
COPY lambdas/music_store_agents/state.py            agents/
COPY lambdas/music_store_agents/secrets_helper.py   agents/
COPY lambdas/music_store_agents/preferences_helper.py agents/
COPY lambdas/music_store_agents/nodes/              agents/nodes/
COPY lambdas/music_store_agents/tools/              agents/tools/

# Copy Gradio application
COPY gradio_app/app.py .

EXPOSE 7860

CMD ["python", "app.py"]
