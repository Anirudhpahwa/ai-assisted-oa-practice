# AI-Assisted OA Practice

Practice mocks for **AI-assisted coding online assessments** (also called AI-assisted repository debugging tasks). In this format you get an unfamiliar full-stack repo with failing tests and an AI assistant in the editor. You have about 60 minutes to find the bugs and make the tests pass.

This kind of round is reported by candidates for software engineering internship and new-grad roles at large tech companies such as Amazon and Microsoft. These mocks are original practice material inspired by the general format. They are not affiliated with or endorsed by any company, and they contain no real assessment content.

Each mock is a small React + Django app. The bugs are all in the Django backend. Every test fails when you start.

## Mocks

| Mock | Domain | Tests | Stack | Download |
|---|---|---|---|---|
| [mock-01-returns-desk](mock-01-returns-desk) | Returns desk: returns, items, status workflow | 6 | React + Django + pytest | [zip](https://github.com/Anirudhpahwa/ai-assisted-oa-practice/releases/latest/download/mock-01-returns-desk.zip) |
| [mock-02-leave-desk](mock-02-leave-desk) | Leave desk: time-off requests, balances, approvals | 6 | React + Django + pytest | [zip](https://github.com/Anirudhpahwa/ai-assisted-oa-practice/releases/latest/download/mock-02-leave-desk.zip) |

Solutions live in a separate repo so they don't show up while you practice: [ai-assisted-oa-practice-solutions](https://github.com/Anirudhpahwa/ai-assisted-oa-practice-solutions). Open them only after you finish.

## How to practice

1. **Get one mock.** Click its **zip** link in the table above and unzip it. (Or use Code, then Download ZIP for the whole repo and take one folder.)
2. **Open that mock's folder in VS Code** (File, then Open Folder). Open the mock folder itself, not the repo root.
3. **Install and run the tests** from inside the mock folder:
   ```
   python -m venv venv
   venv\Scripts\activate        # macOS/Linux: source venv/bin/activate
   pip install -r requirements.txt
   pytest
   ```
   All tests should fail at first.
4. **Start a 60-minute timer.** Read the mock's `README.md` first, then the tests.
5. **Use an AI assistant in your editor** (Claude Code, Copilot Chat, Cursor or similar). Tell it: "Read the files in this repo." It will find `AI_ASSISTANT_RULES.md` and act as a read-only assessment assistant that points you at likely problems but never edits your code.
6. **Make every edit yourself.** Don't run the frontend. It is there for reference only.
7. When the timer ends or all tests pass, check your fixes against the solutions repo.

About 10 minutes per test is a good pace for a 6-test mock.

## Contributing

Found a mock where a test is unfair, or the README doesn't define a tested behavior? Open an issue.

## License

[MIT](LICENSE)
