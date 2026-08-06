---
paths:
  - "infra/**"
  - "terraform/**"
  - "deploy/**"
  - "docker/**"
  - "k8s/**"
  - ".github/workflows/**"
  - "Dockerfile"
  - "docker-compose*.yml"
  - "*.tf"
---

# Infrastructure & DevOps Best Practices (Example Sector-Specific Rule)

> This is an EXAMPLE path-scoped rule for infrastructure, CI/CD, and deployment
> code. Copy and adapt for your project. Only loads when editing matching files.

## Containers
- Use multi-stage builds to minimize image size
- Pin base image versions (e.g., `node:20.11-alpine`, not `node:latest`)
- Run as non-root user in production containers
- Use `.dockerignore` to exclude build artifacts, tests, and secrets

## Infrastructure as Code
- All infrastructure must be defined in code (Terraform, Pulumi, CloudFormation, etc.)
- No manual changes to production resources — all changes go through IaC
- Use remote state with locking (e.g., S3 + DynamoDB for Terraform)
- Tag all resources with project, environment, and owner

## CI/CD Pipelines
- Every PR must pass lint, test, and build before merge
- Use separate stages: build, test, security scan, deploy
- Pin action/plugin versions in CI config (no `@latest` or `@main`)
- Store secrets in CI secret management — never in pipeline files

## Security
- Scan container images for vulnerabilities (Trivy, Snyk, etc.)
- Rotate credentials and access keys on a schedule
- Use least-privilege IAM roles for CI runners and services
- Enable audit logging on all production infrastructure

## Monitoring & Observability
- Every service must expose health check endpoints
- Configure alerts for error rate, latency, and resource utilization
- Use structured logging (JSON) with consistent fields across services
- Set up dashboards for critical paths before deploying new features

## Disaster Recovery
- Document recovery procedures for each production service
- Test backups regularly — an untested backup is not a backup
- Define and document RPO (Recovery Point Objective) and RTO (Recovery Time Objective)
