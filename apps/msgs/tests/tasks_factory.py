from django.test import SimpleTestCase
from dramatiq.actor import Actor


class TasksFactoryTestCase(SimpleTestCase):
    def _get_task_methods(self):
        import apps.msgs.tasks as tasks
        tasks_dict = {}
        for name in dir(tasks):
            maybe_task = getattr(tasks, name, None)
            if maybe_task and isinstance(maybe_task, Actor):
                tasks_dict[name] = maybe_task
        return tasks_dict

    def test_all_tasks_are_created(self):
        tasks_dict = self._get_task_methods()
        self.assertTrue(bool(tasks_dict), 'There are no dramaiq-tasks created!')

    def test_proper_number_of_tasks_created(self):
        from django.conf import settings
        msg_conf = settings.MESSAGES_PROVIDERS
        tasks_dict = self._get_task_methods()
        self.assertTrue(len(tasks_dict) >= len(msg_conf), f'Not all tasks are created! {tasks_dict}')
