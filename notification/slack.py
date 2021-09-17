import os
import json
import urllib.request as urq


def send_notification(message: str, SLACK_HOOK_CHANNEL=None, SLACK_HOOK_URL=None, use_env_vars=True):
    if use_env_vars:
        should_send = os.environ.get("SEND_NOTIFICATIONS")

        if should_send:
            channel = os.environ.get("SLACK_HOOK_CHANNEL")
            url = os.environ.get("SLACK_HOOK_URL")

            data = {"channel": channel, "text": message}

            req = urq.Request(
                url=url,
                method="POST",
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )

            urq.urlopen(url=req)

    else:
        data = {"channel": SLACK_HOOK_CHANNEL, "text": message}
        req = urq.Request(
            url=SLACK_HOOK_URL,
            method="POST",
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        urq.urlopen(url=req)
