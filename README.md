# Coderift

**Catch issues. Fix faster. Never leave your editor.**

Coderift is a VS Code extension that delivers real-time, AI-driven diagnostics and one-click refactoring suggestions — no context switching, no PR delays.

## Features (v0.0.4)

- **Real-time Analysis** — Instant fix suggestions via the `coderift.review` command
- **Intelligent Diagnostics** — Detects logic flaws, code smells, and bugs with context-aware analysis
- **One-Click Refactoring** — Apply AI suggestions using native VS Code Quick Fixes
- **Secure Config** — Bring your own OpenAI API key; analysis stays private

## Architecture

| Layer | Stack |
| :--- | :--- |
| **Extension** | TypeScript, VS Code Extension API |
| **Backend** | Python, FastAPI (hosted on Railway) |
| **AI Engine** | OpenAI GPT-4o, prompt engineering |
| **DevOps** | GitHub Actions, VS Code Marketplace |

## Roadmap

- ✅ **Phase 1** — Core VS Code extension with real-time diagnostics
- 🔄 **Phase 2** — GitHub PR Agent: automated PR reviews via webhooks *(in development)*
- 🔲 **Phase 3** — Multi-file context analysis and custom coding standards

## Getting Started

1. Install from the [VS Code Marketplace](https://marketplace.visualstudio.com/items?itemName=AdityaMurali.coderift)
2. Add your OpenAI API key under **Settings → Coderift**
3. Open any Python file and run `Coderift: Review Current File` (`Cmd+Shift+P`)
4. Hover over diagnostics → click **Quick Fix** to apply suggestions

## License

MIT — see `LICENSE` for details.

---

Built by [Aditya Murali](https://github.com/adityamurali99)