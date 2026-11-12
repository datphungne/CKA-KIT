FROM python:3.12-slim-bookworm
ARG TARGETARCH
# Keep KUBECTL_VERSION in step with the node image pinned in cluster/create-kind.sh.
ARG KIND_VERSION=v0.33.0
ARG KUBECTL_VERSION=v1.37.0
ARG HELM_VERSION=v3.22.1
RUN apt-get update && apt-get install -y --no-install-recommends bash bash-completion ca-certificates curl docker.io vim-tiny less procps git openssl && rm -rf /var/lib/apt/lists/*
RUN set -eux; arch="${TARGETARCH:-amd64}"; \
    curl -fsSLo /usr/local/bin/kind "https://kind.sigs.k8s.io/dl/${KIND_VERSION}/kind-linux-${arch}"; \
    curl -fsSLo /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${arch}/kubectl"; \
    curl -fsSLo /tmp/kubectl.sha256 "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${arch}/kubectl.sha256"; \
    echo "$(cat /tmp/kubectl.sha256)  /usr/local/bin/kubectl" | sha256sum -c -; \
    curl -fsSLo /tmp/helm.tar.gz "https://get.helm.sh/helm-${HELM_VERSION}-linux-${arch}.tar.gz"; \
    tar -xzf /tmp/helm.tar.gz -C /tmp; mv "/tmp/linux-${arch}/helm" /usr/local/bin/helm; \
    chmod +x /usr/local/bin/kind /usr/local/bin/kubectl /usr/local/bin/helm; rm -rf /tmp/linux-* /tmp/helm.tar.gz /tmp/kubectl.sha256
WORKDIR /workspace
COPY web/server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY . .
RUN find . \( -name '*.sh' -o -name '*.bashrc' \) -exec sed -i 's/\r$//' {} + && mkdir -p answers /lab \
    && ln -sf /usr/bin/vim.tiny /usr/local/bin/vim
ENV PYTHONUNBUFFERED=1
ENV DOCKER_API_VERSION=1.44
ENTRYPOINT ["bash", "/workspace/web/entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "--app-dir", "web/server", "app:app", "--host", "0.0.0.0", "--port", "8765", "--no-access-log"]
