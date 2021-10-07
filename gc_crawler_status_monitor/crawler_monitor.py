from .config import Config
from dataPipelines.gc_db_utils.orch.models import CrawlerStatusEntry
from textwrap import dedent
import datetime
from sqlalchemy.sql.expression import func

from notification.slack import send_notification


class CrawlerMonitor:
    def check_for_stale_statuses(self):

        Config.connection_helper.init_orch_db()
        with Config.connection_helper.orch_db_session_scope('rw') as session:
            current_time = datetime.datetime.utcnow()

            eight_days_ago = current_time - datetime.timedelta(days=8)

            overdue = session.query(
                CrawlerStatusEntry.crawler_name,
                func.max(CrawlerStatusEntry.datetime).label('datetime')
            ).filter(
                (CrawlerStatusEntry.status == "Ingest Complete")
            ).group_by(
                CrawlerStatusEntry.crawler_name
            ).all()

            if not overdue:
                return

            print('overdue', overdue)
            warnings = "\n".join(
                [
                    f"`{crawler.crawler_name}` was last run `{crawler.datetime.strftime('%b %d %Y')}`"
                    for crawler in overdue if crawler.datetime < eight_days_ago
                ]
            )
            message = dedent(f"""
            ![WARNING] - MONITORING: CRAWLERS OVERDUE\n{warnings}
            """)

            send_notification(message)
