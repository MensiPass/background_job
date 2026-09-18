# FastAPI Background Jobs with Inngest

A small FastAPI application demonstrating asynchronous background jobs with the Inngest Python SDK.

The project demonstrates:

* FastAPI API endpoints
* Inngest event-driven background jobs
* delayed background execution
* report status polling
* retries
* failure handling
* scheduled cron functions
* in-memory report storage

## Requirements

* Python 3.12+
* FastAPI
* Inngest Python SDK 0.5.19

## Run the project

### Terminal 1 — FastAPI

Activate the virtual environment and start FastAPI:

```bash
INNGEST_DEV=1 python -m fastapi dev main.py --port 8001
```

On Windows PowerShell, you can also use:

```powershell
$env:INNGEST_DEV="1"
python -m fastapi dev main.py --port 8001
```

### Terminal 2 — Inngest Dev Server

Start the Inngest Dev Server using the command configured for your local Inngest setup.

The FastAPI application exposes the Inngest endpoint at:

```text
http://localhost:8001/api/inngest
```

## API

### Health check

```http
GET /health
```

Example:

```bash
curl.exe http://localhost:8001/health
```

Response:

```json
{
  "status": "ok"
}
```

### Create a report

```http
POST /reports
```

Request:

```json
{
  "topic": "success"
}
```

Example:

```bash
curl.exe -X POST http://localhost:8001/reports -H "Content-Type: application/json" -d "{\"topic\":\"success\"}"
```

The API immediately returns:

```json
{
  "id": "REPORT_ID",
  "status": "pending"
}
```

The report is processed asynchronously by Inngest.

### Get report status

```http
GET /reports/{report_id}
```

Example:

```bash
curl.exe http://localhost:8001/reports/REPORT_ID
```

A completed report returns:

```json
{
  "topic": "success",
  "status": "done",
  "result": "Report generated for success"
}
```

## Failure and retries

Sending the topic `"fail"` intentionally causes the background job to fail:

```bash
curl.exe -X POST http://localhost:8001/reports -H "Content-Type: application/json" -d "{\"topic\":\"fail\"}"
```

The `make-report` function is configured with:

```python
retries=2
```

This means the initial execution plus two retries can occur.

After the retries are exhausted, the `on_failure` handler changes the report status to:

```json
{
  "topic": "fail",
  "status": "failed"
}
```

The failure handler receives the Inngest `function.failed` event. The original report ID is nested inside:

```python
ctx.event.data["event"]["data"]["report_id"]
```

## Scheduled heartbeat

The project also contains a cron function:

```python
cron="* * * * *"
```

It runs approximately every minute and prints:

```text
HEARTBEAT: pending=0, done=1, failed=1
```

The heartbeat counts reports currently stored in memory.

### Cron examples

```text
0 8 * * *
```

Runs every day at 08:00.

```text
0 22 * * 0
```

Runs every Sunday at 22:00.

Cron fields are:

```text
minute hour day-of-month month day-of-week
```

## Inngest functions

| Function                | Trigger               | Purpose                                         |
| ----------------------- | --------------------- | ----------------------------------------------- |
| `say-hello`             | `test/hello`          | Demonstrates a delayed background function      |
| `make-report`           | `report/requested`    | Generates reports asynchronously                |
| `heartbeat`             | Cron                  | Periodically reports pending/done/failed counts |
| `make-report (failure)` | Inngest failure event | Marks failed reports as `failed`                |

## Project flow

Successful report:

```text
POST /reports
     ↓
report/requested
     ↓
make-report
     ↓
8 second delay
     ↓
build-report
     ↓
status = done
```

Failed report:

```text
POST /reports
     ↓
report/requested
     ↓
make-report
     ↓
build-report
     ↓
failure
     ↓
retry
     ↓
retry
     ↓
on_failure
     ↓
status = failed
```

## Verification

The project has been tested with:

* successful report execution
* intentionally failed report execution
* retry handling
* `on_failure` handling
* report status polling
* scheduled heartbeat execution

The Inngest dashboard shows successful completion for the successful path, failed execution followed by failure handling for the failure path, and completed heartbeat executions.

## Current limitations

This is a learning/demo project.

Report data is stored in an in-memory Python dictionary:

```python
reports = {}
```

Therefore report data is lost when the FastAPI process restarts.

There is no authentication, database persistence, queue worker infrastructure, or production deployment configuration.
