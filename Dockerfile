FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --uid 1000 appuser \
  && chown -R appuser:appuser /app

COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV HOME=/home/appuser

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
