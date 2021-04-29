ARG BASE_IMAGE='gamechanger/core/ci-env:latest'
FROM $BASE_IMAGE

ENV APP_REPO=/app
RUN mkdir -p "$APP_REPO"
COPY . "$APP_REPO"
WORKDIR "$APP_REPO"