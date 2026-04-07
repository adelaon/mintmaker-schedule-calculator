FROM registry.access.redhat.com/ubi10/python-312-minimal@sha256:3dc047bf30c6dac75b7a74aebcb8944ce35f46cc421543d9ce74716d2a6e611e

WORKDIR /opt/app-root/src

USER 0
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir uv

USER 1001

COPY --chown=1001:0 pyproject.toml uv.lock README.md ./
COPY --chown=1001:0 src ./src

RUN uv sync --frozen --no-dev

ENV VIRTUAL_ENV=/opt/app-root/src/.venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

CMD ["python", "-m", "mintmaker_schedule_calculator"]

