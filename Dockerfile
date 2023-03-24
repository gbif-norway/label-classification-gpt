FROM golang:1.19.3-alpine AS build
WORKDIR /app
COPY . ./
RUN go mod download
RUN go build -o /label-classification-gpt

## Deploy
FROM alpine:3
WORKDIR /
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
COPY --from=build /label-classification-gpt /label-classification-gpt
ENTRYPOINT [ "/label-classification-gpt" ]
