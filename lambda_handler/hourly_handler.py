from automation import run_hourly_pipeline

def lambda_handler(event, context): # type: ignore
    """AWS Lambda entry point for hourly updates"""
    print("Running hourly pipeline...")
    run_hourly_pipeline()
    return {"status": "ok"}
