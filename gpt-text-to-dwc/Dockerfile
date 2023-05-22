FROM golang:1.19.3-alpine AS build
WORKDIR /app
COPY ./code ./
RUN go mod download
RUN go build -o /gpt-text-to-dwc

## Deploy
FROM alpine:3
WORKDIR /
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
COPY --from=build /gpt-text-to-dwc /gpt-text-to-dwc
ENTRYPOINT [ "/gpt-text-to-dwc" ]