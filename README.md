# Exam Management System

Plans a university exam period:

- **Schedule**: which paper is written on which day and session.
- **Seating**: where every student sits.
- **Duties**: which teachers supervise each room.

All three are done by hand today, and students end up with two exams on the same day.

Course project for CSE3005 Software Engineering, BML Munjal University, 2026–27.

## Team

| Who | Works on |
|---|---|
| Ishan Batra | Maintainer: reviews and merges every pull request, and makes releases. |
| Krish Sharma, Himank Swami | Dummy input data and the engine: schedule, seating and duties. |
| Harsh Vardhan, Koushik Araveti | The terminal app for running the tool and changing its settings, the output checker, and the Google Sheets, Gmail and Calendar connectors. |

Each pair splits its own work.

## Folders

| Folder | Contents |
|---|---|
| `prototype1/` | First working version: input folder in, exam plan out. |
| `prototype2/` | Terminal app: pick the inputs and dates, then make the plan. |
| `agents/` | Rules for everyone working here, people and AI assistants, and optional skills. |
| `docs/` | Submitted project plan and the list of decisions. |
| `archive/` | Earlier attempts. Reference only. |

## Contributing

Read [`agents/README.md`](agents/README.md) first. The rules are in `agents/repo_rules.md` and `agents/this_repo.md`.
