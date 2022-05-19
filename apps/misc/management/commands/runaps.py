import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from apps.orders.models import Order
from apps.orders.const import OrderStatus


logger = logging.getLogger(__name__)


def remove_todays_orders():
    Order.objects.filter(status=OrderStatus.NEW).delete()

def delete_old_job_executions(max_age=604_800):
    """This job deletes all apscheduler job executions older than `max_age` from the database."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    help = "Runs apscheduler."

    def handle(self, *args, **options):
        # Можно использовать блокирующий, он никак не повлияет на работоспособность приложения
        # Поскольку блокировка короткосрочная и в тот момент, когда приложение и так не используется
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        scheduler.add_job(
            remove_todays_orders,
            trigger=CronTrigger(hour="00", minute="00"), # Удаляем новые заказы каждую ночь
            id="remove_todays_orders",
            max_instances=1,
            replace_existing=True,
        )

        scheduler.add_job(
            delete_old_job_executions,
            # Удаляем сохранения о выполнении задач каждую неделю
            trigger=CronTrigger(day_of_week="mon", hour="00", minute="00"),
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")
