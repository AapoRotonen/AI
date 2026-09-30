# ADR 0001: Java 21 and Spring Boot 3.5

## Status

Accepted for the Java 21 PoC.

## Context

The brief requires Java 21 and current official Spring APIs. Spring AI 1.1 supports Spring Boot 3.4/3.5, allowing a stable Spring AI release on the requested Java baseline.

## Decision

Pin Spring Boot 3.5.16 and Spring AI 1.1.8. Keep versions managed by Spring Boot and the Spring AI BOM. Revisit both together when moving to Spring Boot 4 / Spring AI 2.

## Consequences

This pair preserves the familiar Boot 3 / Spring Security 6 baseline. Spring Boot 3.5's final OSS patch has passed, so future security maintenance should plan an upgrade to a supported Spring release train.
