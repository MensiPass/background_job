from fastapi import FastAPI
import inngest
import inngest.fast_api

app = FastAPI()

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


inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello],
    serve_path="/api/inngest",
    enable_unauthed_sync=True
)


@app.get("/health")
def health():
    return {"status": "ok"}