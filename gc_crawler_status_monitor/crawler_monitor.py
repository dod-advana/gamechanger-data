from .config import Config
from dataPipelines.gc_db_utils.orch.models import CrawlerStatusEntry
from textwrap import dedent
import datetime

from notification.slack import send_notification


class CrawlerMonitor:
    def check_for_stale_statuses(self):

        Config.connection_helper.init_orch_db()
        with Config.connection_helper.web_db_session_scope('rw') as session:
            current_time = datetime.datetime.utcnow()

            eight_days_ago = current_time - datetime.timedelta(days=8)

            data = session.query(CrawlerStatusEntry).all()

            print('data', data)

            overdue = session.query(CrawlerStatusEntry).filter(
                (CrawlerStatusEntry.status == "Ingest Complete"),
                (CrawlerStatusEntry.datetime < eight_days_ago)
            ).all()

            if not overdue:
                return

            print('overdue', overdue)
            warnings = "\n".join(
                [
                    f"{crawler.crawler_name} was last run {crawler.datetime}"
                    for crawler in data
                ]
            )
            message = dedent(f"""
            ![WARNING] - MONITORING: CRAWLERS OVERDUE
            {warnings}
            """)

            send_notification(message)
