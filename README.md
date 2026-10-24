# milestone2-ai-agent
Context-based AI agent with tool functions and repeatability testing
**Preventing Unsupported Answers:** The agent retrieves information from `context.json` using Python functions and checks whether the question is supported by the available context. If the required information is missing, it returns a predefined fallback message instead of asking the AI model to guess.

**Repeatability Check:** The agent runs the same question twice and compares both answers after normalizing capitalization and whitespace. If the answers match, the check returns PASS; otherwise, it returns FAIL.
