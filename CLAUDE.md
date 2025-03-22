# MCP Outline Server Guide

This guide helps Claude implement and modify the MCP Outline server codebase effectively.

## 1. Purpose & Overview

This MCP server enables AI assistants to interact with Outline by:
- Connecting to Outline services via REST API
- Exposing Outline data (documents, collections, comments)
- Providing tools to create and modify Outline objects
- Using API key authentication for secure interactions

## 2. Core Concepts

### Outline & MCP Integration

This project bridges two systems:

1. **Outline Objects**:
   - Documents (content, metadata)
   - Collections (grouping of documents)
   - Comments on documents
   - Document structure and hierarchy

2. **MCP Components**:
   - **Tools**: Functions that interact with Outline API

## 3. Implementation Guidelines

### Tools Implementation
- Create tool functions for each Outline API endpoint
- Follow existing patterns in the `features/documents/` directory
- Keep functions simple with clear purposes
- Handle authentication and errors properly
- Example implementations: `search_documents`, `create_document`

### Development Workflow
1. Review the Outline API documentation
2. Use simple HTTP requests to the API
3. Follow existing patterns and code style
4. Keep the KISS principle in mind

## 4. Technical Requirements

### Code Style
- PEP 8 conventions
- Type hints for all functions
- Line length: 79 characters
- Small, focused functions

### Development Tools
- Install: `uv pip install -e ".[dev]"`
- Run server: `mcp dev src/mcp_outline/server.py`
- Run tests: `uv run pytest tests/`
- Format: `uv run ruff format .`

### Critical Requirements
- No logging to stdout/stderr
- Import sorting: standard library → third-party → local
- Proper error handling with specific exceptions
- Follow the KISS principle
