# ADR 0004: Require human approval for AI-proposed state changes

## Status

Accepted.

## Decision

The initial write workflow supports only a close-ticket proposal. Java policy creates a pending HumanReview. A distinct senior/admin reviewer decides it. Java performs closure only after approval.

## Consequences

The AI can make a proposal but cannot close a ticket, choose whether review is needed, or approve itself. Other writes remain out of scope.
