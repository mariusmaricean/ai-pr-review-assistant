from app.worker import celery_app


@celery_app.task(name="review_pull_request")
def review_pull_request(payload: dict):
    print("Received PR review job")
    print(payload)

    return {"status": "queued_payload_received"}
