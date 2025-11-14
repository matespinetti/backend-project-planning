# AGENTS.md — ProjectPlanning FastAPI Proxy API (System Instructions)

## Overview

You are an AI assistant working inside the **ProjectPlanning FastAPI Proxy API**.  
Your role is to help generate clean, consistent, and well-structured code and documentation for a **stateless orchestration API** that sits between:

-   **Next.js Frontend**
-   **Cloud Persistence API** (owner of JWT authentication + PostgreSQL)
-   **Bonita BPM** (workflow engine)

This API **does not** store data locally and **does not** manage users.  
Its entire job is to **validate input**, **forward requests**, and **orchestrate workflows**.

---

## Core Principles

### 1. Stateless Proxy

-   No database.
-   No ORM.
-   No persistence layer.
-   No business logic beyond orchestration and request validation.

### 2. One Frontend → One Backend

The frontend must talk **only to this proxy API**.  
The proxy decides whether to call:

-   Cloud API
-   Bonita BPM
-   Or both (in orchestrated flows)

### 3. JWT From Cloud API

-   The Cloud API handles authentication and issues JWTs.
-   The proxy API:
    -   **validates** the JWT (shared secret)
    -   **forwards** it to the Cloud API
    -   uses it to determine `user_id`, roles, etc.

### 4. Error-First Mindset

-   If an external service fails, return a clean error to the frontend.
-   Log all context.
-   Rollback when needed (ex: project creation).

---

## Required Behaviors

### Project Creation (`POST /api/v1/projects`)

-   Validate with Pydantic.
-   Forward creation to Cloud API → get real UUID.
-   Start Bonita process with that UUID.
-   If Bonita fails → rollback in Cloud API.
-   If everything succeeds → return combined response.

### Get Project (`GET /api/v1/projects/{id}`)

-   Validate UUID.
-   Forward GET to Cloud API.
-   Return result as-is (normalized errors).

---

## Tech Stack Requirements

-   **FastAPI**
-   **Pydantic v2**
-   **httpx.AsyncClient**
-   **uv (package manager)**
-   **Docker-ready**
-   Clean async code.

---

## Coding Standards

-   Strict typing (`from __future__ import annotations`).
-   Use async everywhere.
-   Each external service has its own client:
    -   `BonitaClient`
    -   `CloudAPIClient`
-   No duplicate logic: thin proxy where possible.
-   Use settings via `pydantic-settings`.
-   Consistent error responses:
    -   `422` → validation
    -   `404` → not found (proxied)
    -   `500` → orchestration / external failures

---

## Folder Structure (Expected)

app/
main.py
config.py
api/v1/endpoints/projects.py
core/bonita.py
core/cloud_client.py
schemas/

---

## What You Should Generate

When asked, you may produce:

-   FastAPI endpoint code
-   Pydantic schemas
-   Cloud/Bonita client implementations
-   Clean folder structures
-   Orchestration flows
-   Error-handling patterns
-   Configuration templates
-   Docker setups
-   Short explanations for the report

---

## What You Should NOT Generate

-   No local database models
-   No SQL
-   No ORM logic
-   No stored state
-   No authentication system (JWT is Cloud API’s responsibility)

---

## Goal

Ensure the proxy API:

-   stays **small**,
-   stays **stateless**,
-   stays **clean**,
-   orchestrates between services correctly,
-   and exposes a **simple, stable contract** to the Next.js frontend.
