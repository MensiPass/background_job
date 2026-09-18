from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
import uuid
import inngest
import inngest.fast_api


app = FastAPI()


class ReportRequest(BaseModel):
    topic: str


reports = {}


inngest_client = inngest.Inngest(
    app_id="report-api",
    is_production=False
)


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(
        event="test/hello"
    )
)
async def say_hello(ctx: inngest.Context):
    await ctx.step.sleep(
        "wait",
        5000
    )

    return "Hello from the background!"

async def handle_report_failure(ctx: inngest.Context):
    report_id = ctx.event.data["event"]["data"]["report_id"]
    reports[report_id]["status"] = "failed"

@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(
        event="report/requested"
    ),
    retries=2,
    on_failure=handle_report_failure,
)
async def make_report(ctx: inngest.Context):
    report_id = ctx.event.data["report_id"]

    await ctx.step.sleep(
        "wait",
        8000
    )

    async def build_report():
        if reports[report_id]["topic"] == "fail":
            raise Exception("Report generation failed")

        return f"Report generated for {reports[report_id]['topic']}"

    result = await ctx.step.run(
        "build-report",
        build_report
    )

    reports[report_id]["status"] = "done"
    reports[report_id]["result"] = result

    return reports[report_id]

@app.post("/reports", status_code=202)
async def create_report(request: ReportRequest):
    report_id = str(uuid.uuid4())

    reports[report_id] = {
        "topic": request.topic,
        "status": "pending"
    }

    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={
                "report_id": report_id
            }
        )
    )

    return {
        "id": report_id,
        "status": "pending"
    }

@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    if report_id not in reports:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return reports[report_id]

inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello, make_report],
    serve_path="/api/inngest",
    enable_unauthed_sync=True
)


@app.get("/health")
def health():
    return {"status": "ok"}