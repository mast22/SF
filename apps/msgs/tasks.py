
def __create_tasks():
    from .tasks_factory import TasksFactory
    tf = TasksFactory()
    all_tasks = tf.create_all_tasks()
    g = globals()
    for task_name, task in all_tasks.items():
        task_name = task_name.strip().replace('.', '_') + '_task'
        task.__name__ = task_name
        g[task_name] = task
    return all_tasks


__create_tasks()
