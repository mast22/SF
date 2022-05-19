import dramatiq
import rollbar


class RollbarMiddleware(dramatiq.Middleware):
    def after_process_message(self, broker, message, *, result=None, exception=None):
        if exception is not None:
            rollbar.report_exc_info()
