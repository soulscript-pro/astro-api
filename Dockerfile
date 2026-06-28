FROM python:3.11-slim
RUN apt-get update && apt-get install -y libsqlite3-dev gcc build-essential wget && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00002s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00003s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00004s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00010s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00011s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00016s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00097s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00120s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00157s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00174s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00273s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00408s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast0/se00638s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast1/se00433s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast1/se01027s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast1/se01388s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast1/se01862s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast2/se02101s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast2/se02878s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast3/se03811s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast4/se04386s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast4/se04581s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast6/se06583s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast7/se07066s.se1 || true && \
    wget -q -P ephe https://www.astro.com/swisseph/ephe/ast10/se10199s.se1 || true
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-8080}"]
