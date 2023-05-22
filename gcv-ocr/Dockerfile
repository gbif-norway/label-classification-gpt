FROM golang:1.19.3-alpine AS build
WORKDIR /app
COPY ./code ./
RUN go mod download
RUN go build -o /gcv-ocr

## Deploy
FROM alpine:3
WORKDIR /
COPY ./gapi-secret.json /srv/gapi-secret.json
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
COPY --from=build /gcv-ocr /gcv-ocr
ENTRYPOINT [ "/gcv-ocr" ]