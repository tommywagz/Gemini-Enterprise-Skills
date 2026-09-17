# Skill Evaluation Report: gcp-iam-privilege-audit

**Date:** 2026-09-17  
**Evaluator:** evaluator  
**Iteration:** 2 (of 3)

## Summary

Ship. The standard-library Recommender client passed mock mode, routing passed all 20 balanced cases, and the skill confines itself to review-only IAM recommendations and Terraform snippets.

## Risk Tier

**High**

Live mode performs one authenticated, read-only Recommender REST request using a stdin-only bearer token; no credentials are persisted and no IAM mutation is available.

## Metrics

`score_eval_suite.py`: 20 graded, TP=10, FP=0, TN=10, FN=0; precision=100%, recall=100%, FPR=0%, assertions=100%. Mock client: passed. Script compilation and security scan: passed. Body is under the 5,000-token limit.

## Findings & Fixes

Added an explicit unavailable-reference fallback to prevent inferred IAM role mappings. The body already declares Confidential handling for policy and service-account data and prohibits key/token disclosure.

## Security Review

The client uses `urllib` only for the documented Recommender read endpoint and receives its token through stdin. It does not invoke `gcloud`, Terraform apply, or policy/key mutation commands. Treat the resulting IAM inventory and recommendations as Confidential. No irreversible action is available, so no approval is needed for the skill itself.

## Remaining Gaps

Validate proposed binding changes in a non-production project and obtain IAM SME review before applying any human-approved change.
