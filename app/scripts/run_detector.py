from app.workers.tasks_detect import enqueue_poll_mentions


if __name__ == "__main__":
    enqueue_poll_mentions.delay()
