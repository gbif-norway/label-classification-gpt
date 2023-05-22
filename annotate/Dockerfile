FROM golang:1.19.3-alpine AS build
WORKDIR /app
COPY ./code ./
RUN go mod download
RUN go build -o /annotate

## Deploy
FROM alpine:3
WORKDIR /
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
COPY --from=build /annotate /annotate
ENTRYPOINT [ "/annotate" ]