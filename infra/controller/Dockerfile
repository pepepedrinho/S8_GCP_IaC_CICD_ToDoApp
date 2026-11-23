FROM python:3.13-slim-bookworm
ENV DEBIAN_FRONTEND=noninteractive PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg openssh-client rsync git jq unzip && \
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    echo 'deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main' > /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && apt-get install -y --no-install-recommends google-cloud-cli && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir ansible-core==2.19.4 ansible-lint==25.11.1
RUN ansible-galaxy collection install ansible.posix:2.1.0
WORKDIR /workspace
CMD ["bash"]
