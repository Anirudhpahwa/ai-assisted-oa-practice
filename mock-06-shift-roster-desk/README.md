# Shift Roster Desk (C++17)

A small command-line tool for a store that staffs its shifts. Staff members ask to take shifts. The tool reads the staff list, the open shifts, the requests and a few house rules, decides each request in order, works out the pay for every approved shift, and writes a results file and a per-person summary.

The code lives in `src/`, the tests in `tests/`. The tests call the functions described below directly, so the whole program is covered by them.

## Input files

All files are plain text. Lines end with `\n` or `\r\n`. The three `.csv` files share these rules:

- The first line is a header and is always skipped. Blank lines are skipped.
- Fields are separated by commas, and each field has its leading and trailing whitespace removed.
- A row with the wrong number of fields is an error, and so is a field that does not match its format.
- Errors are reported by throwing `ParseError`. Its message starts with `<kind> line <n>:`, where `<kind>` is `staff`, `shifts`, `requests` or `rules`, and `<n>` is the line number in the file (the header is line 1).

**staff.csv**: `staff_id,name,role,max_weekly_minutes,hourly_rate_cents`

- `max_weekly_minutes` and `hourly_rate_cents` are whole numbers of 0 or more.

**shifts.csv**: `shift_id,date,start,end,role`

- `date` is `YYYY-MM-DD` and must be a real date. `start` and `end` are `HH:MM` on a 24-hour clock. `end` must be after `start`, and a shift never crosses midnight.
- A shift is converted to `Shift`: `day` is the number of days since 1970-01-01, `start` and `end` are minutes after midnight, and `minutes()` is its length.

**requests.csv**: `request_id,staff_id,shift_id`

**rules.cfg**: one `key=value` per line.

- Blank lines and lines starting with `#` are skipped. The key and the value are trimmed. The value is a whole number of 0 or more.
- Keys, with defaults: `min_rest_minutes` (660), `overtime_after_minutes` (2400), `overtime_pct` (150). Any other key is an error.

## Dates

- `days_from_civil(year, month, day)` returns the number of days since 1970-01-01, so 1970-01-01 is 0.
- `week_index(days)` returns the number of the week that a day (in that same unit) falls in. Weeks run from Monday to Sunday: every day in one week has the same index, and the next week's index is one higher.

## Deciding requests

`decide_all(staff, shifts, requests, rules)` handles the requests in the order given and returns one `Decision` per request, in the same order. For each request the first rule that applies decides it:

1. `UNKNOWN_STAFF`: no staff member has that `staff_id`.
2. `UNKNOWN_SHIFT`: no shift has that `shift_id`.
3. `ROLE_MISMATCH`: the shift's `role` differs from the staff member's `role`.
4. `SHIFT_TAKEN`: an earlier request already got this shift approved.
5. `OVERLAP`: the shift overlaps a shift already approved for the same person. Shifts that only touch (one ends exactly when the other starts) do not overlap.
6. `INSUFFICIENT_REST`: the time between this shift and a shift already approved for the same person, counted from the end of the earlier one to the start of the later one, is less than `min_rest_minutes`. This applies across days. A gap of exactly `min_rest_minutes` is allowed.
7. `WEEKLY_LIMIT`: the person's approved minutes in the same week plus this shift's minutes would be more than their `max_weekly_minutes`. A total exactly equal to the limit is allowed. Weeks run from Monday to Sunday.

If none applies the request is approved. Only an approved request changes anything: a rejected request never reserves a shift or counts toward anyone's hours.

A `Decision` has `request_id`, `staff_id`, `shift_id`, `approved`, `reason` (empty when approved), `minutes` (the shift's length when approved, otherwise 0) and `pay_cents` (the pay for that shift when approved, otherwise 0).

## Pay

`shift_pay(hourly_rate_cents, week_minutes_before, shift_minutes, rules)` returns the pay in cents for one shift. `week_minutes_before` is how many minutes the person already has approved in the same week, not counting this shift.

- The shift's minutes that fall beyond `overtime_after_minutes` for the week are overtime. The rest are regular. A shift can be partly regular and partly overtime.
- Regular minutes are paid at the hourly rate. Overtime minutes are paid at `overtime_pct` percent of the hourly rate.
- Pay is rounded half up to a whole cent.

For example, at 2000 cents per hour, a full 480-minute shift with nothing before it pays 16000, and the same shift when the week already has 2160 minutes (240 regular, 240 overtime at 150 percent) pays 20000.

## Output

`summarize(staff, decisions)` returns one `StaffSummary` per person with at least one approved request: `staff_id`, `name`, `shifts` (approved count), `minutes` and `pay_cents` (sums over the approved requests). Rows are ordered by `pay_cents` (largest first), ties broken by `staff_id` A to Z.

`format_results(decisions)` returns text with the header `request_id,decision,reason,pay_cents` and one line per decision: `<request_id>,APPROVED,,<pay_cents>` or `<request_id>,REJECTED,<reason>,0`.

`format_summary(summaries)` returns text with the header `staff_id,name,shifts,minutes,pay_cents` and one line per summary. Every line, including the header, ends with `\n`.

## Running the tests

You need `g++` with C++17 support on your PATH. From the project root:

```
test.bat        (Windows)
./test.sh       (macOS / Linux)
```

The script builds and runs the tests. There is also `run.bat` / `run.sh`, which runs the program on the sample files in `data/sample` and writes the results to `out/`.
