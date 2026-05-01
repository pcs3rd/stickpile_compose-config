FROM golang:1.22-alpine AS build
RUN apk add --no-cache git
RUN go install github.com/adnanh/webhook@latest

FROM alpine:3.19
RUN apk add --no-cache git ca-certificates
COPY --from=build /go/bin/webhook /usr/local/bin/webhook
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh /hooks/pull.sh 2>/dev/null || true
ENTRYPOINT ["/entrypoint.sh"]
