# Troubleshooting

## Server not connecting?

**Check your API credentials:**
```bash
# Test your API key
curl -H "Authorization: Bearer YOUR_API_KEY" YOUR_OUTLINE_URL/api/auth.info
```

Common issues:
- Verify `OUTLINE_API_KEY` is set correctly in your MCP client configuration
- Check `OUTLINE_API_URL` points to your Outline instance (default: `https://app.getoutline.com/api`)
- For self-hosted Outline, ensure the URL ends with `/api`
- Verify your API key hasn't expired or been revoked

## Tools not appearing in client?

- **Read-only mode enabled?** Check if `OUTLINE_READ_ONLY=true` is disabling write tools
- **Delete operations disabled?** Check if `OUTLINE_DISABLE_DELETE=true` is hiding delete tools
- **AI tools missing?** Check if `OUTLINE_DISABLE_AI_TOOLS=true` is disabling AI features
- **Dynamic filtering enabled?** If `OUTLINE_DYNAMIC_TOOL_LIST=true`, tools are filtered by user role/key scopes
- Restart your MCP client after changing environment variables

## API rate limiting errors?

The server automatically handles rate limiting with retry logic. If you see persistent rate limit errors:
- Reduce concurrent operations
- Check if multiple clients are using the same API key
- Contact Outline support if limits are too restrictive for your use case

## Docker container issues?

**Container won't start:**
- Ensure `OUTLINE_API_KEY` is set: `docker run -e OUTLINE_API_KEY=your_key ...`
- Check logs: `docker logs <container-id>`

**Can't connect from client:**
- Use `0.0.0.0` for MCP_HOST: `-e MCP_HOST=0.0.0.0`
- Verify port mapping: `-p 3000:3000`
- Check transport mode: `-e MCP_TRANSPORT=streamable-http`

## Need more help?

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Report an issue](https://github.com/Vortiago/mcp-outline/issues)
