# Google Workspace OAuth Scopes

Prefer narrow scopes and request them incrementally at the tool action.

| API | Narrow read scope | Write/send scope | Note |
|---|---|---|---|
| Drive | `https://www.googleapis.com/auth/drive.readonly` | `https://www.googleapis.com/auth/drive.file` for app-created/opened files | `drive` grants broad full access; avoid unless justified. |
| Sheets | `https://www.googleapis.com/auth/spreadsheets.readonly` | `https://www.googleapis.com/auth/spreadsheets` | Bind tool to explicit spreadsheet IDs where possible. |
| Gmail | `https://www.googleapis.com/auth/gmail.readonly` | `https://www.googleapis.com/auth/gmail.send` | Mail scope is sensitive; user confirmation before send remains needed. |
| Calendar | `https://www.googleapis.com/auth/calendar.events.readonly` | `https://www.googleapis.com/auth/calendar.events` | Limit tool behavior to requested calendars/events. |

Scope availability, sensitivity classification, and verification requirements
can change. Confirm current Google OAuth scope documentation and consent
screen requirements before production registration.
