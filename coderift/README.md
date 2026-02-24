# Coderift

Graph-augmented code review powered by GPT-4o. Catches bugs, security flaws, and logic errors that linters miss — without leaving your editor.

---

## Features

- **Instant Review** — Analyze your current file with a single command.
- **AI Quick Fixes** — Apply fixes inline via the 💡 lightbulb. No copy-pasting.
- **Context-Aware** — Understands code dependencies, not just isolated syntax.
- **BYOK** — Your OpenAI key, your data. Full control, full privacy.

---

## Setup

1. Grab an API key from [OpenAI](https://platform.openai.com/api-keys).
2. Open VS Code Settings (`Cmd+,` / `Ctrl+,`).
3. Search **"Coderift"** → paste your key into **Openai Api Key**.

That's it.

---

## Usage

1. Open a Python file.
2. `Cmd+Shift+P` (Mac) / `Ctrl+Shift+P` (Windows) → **"Coderift: Review Current File"**.
3. Issues surface as red squiggles.
4. Hit 💡 or `Cmd+.` / `Ctrl+.` to apply the fix instantly.

---

## Settings

| Setting | Description |
|---|---|
| `coderift.openaiApiKey` | Your OpenAI API key (`sk-...`) |

---

## Privacy

Your code is sent solely for analysis via the OpenAI API. Since you supply the key, you have full visibility into usage through your OpenAI dashboard. No data is stored.

---

*Built by [AdityaMurali]*