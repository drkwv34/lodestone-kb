# SPDX-License-Identifier: Apache-2.0
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE NOTICE ./
COPY src ./src
COPY schemas ./schemas
RUN pip install --no-cache-dir .
USER nobody
ENTRYPOINT ["lodestone", "mcp"]
CMD ["--offline"]
