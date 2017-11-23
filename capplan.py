import collections
import functools

# TODO: Add TaskCollection.append / TaskCollection.prepend / TaskCollection.parallel
from plotters.plotter import MplPlotter


# import matplotlib.pyplot as plt


class PlannerError(Exception):
    pass


class PlanItemMixin:
    @property
    def start(self):
        # latest start date for this task, no slack in this task allows
        if self.end is None:
            return None
        return self.end - self.duration


class Task(PlanItemMixin):
    coll_type = 'task'
    def __init__(self, duration, title=None, resources=None):
        if resources is None:
            resources = []
        self.title = title
        self.estimated_duration = duration
        self.resources = resources
        self.end = None  # absolute latest end date, no slack in this or later tasks allowed
        self.progress = 0.0
        self.on_critical_path = False

    @property
    def duration(self):
        return self.estimated_duration * (1.0 - self.progress)

    def __repr__(self):
        return "<Task " + str(self) + ">"

    def __str__(self):
        if self.title is not None:
            return self.title
        else:
            return "<Task - " + self.duration + ">"

    def tasks(self, resources=None, sort=True):
        if isinstance(resources, str):
            resources = [resources]
        if resources is None or len(self.resources) == 0:
            return [self]
        elif len(set(self.resources) & set(resources)) > 0:
            return [self]
        else:
            return []

    def plan(self, end, next_task=None):
        # plan deadline for this task and return deadline for previous task
        self.end = end
        self.on_critical_path = False
        self.next_task = next_task
        return self.start, self


class AbstractTaskCollection(collections.UserList, PlanItemMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = None
        self.end = None
        self.deadline = None

    @property
    def progress(self):
        if self.end is None:
            return 0
        tasks = self.tasks(sort=False)
        return sum([t.progress * t.duration for t in tasks]) / sum([t.duration for t in tasks])

    def task(self, title):
        for t in self.tasks(sort=False):
            if t.title == title:
                return t
        return None

    def tasks(self, resources=None, sort=True):
        tasks = []
        for d in self.data:
            tasks += d.tasks(resources, sort)
        tasks = list(set(tasks))
        if sort:
            # sorted(student_tuples, key=lambda student: student[2])
            return sorted(tasks, key=lambda t: t.start)
        else:
            return tasks

    def critical_path(self):
        pass

    def plan(self):
        raise NotImplementedError()

    def plan_end(self, end=None):
        if end is None and self.deadline is None:
            raise PlannerError()
        elif end is None and self.deadline is not None:
            self.end = self.deadline
        elif end is not None and self.deadline is not None:
            if end > self.deadline:  # pull back end date to deadline, otherwise might be too late
                self.end = self.deadline
            else:
                self.end = end
        else:
            self.end = end
        return self.end

    @property
    def duration(self):
        raise NotImplementedError()


class SerialTaskCollection(AbstractTaskCollection):
    coll_type = 'serial'
    def __repr__(self):
        return "SerialTaskList <" + str(self) + ">"

    def __str__(self):
        if self.title is not None:
            return self.title
        else:
            return "(" + " - ".join([str(d) for d in self.data]) + ")"

    def plan(self, end=None, next_task=None):
        end = super().plan_end(end)
        for d in reversed(self.data):
            # all plan items must have an end date equal to start date of next task (backwards planning)
            end, next_task = d.plan(end, next_task=next_task)
        return self.start, next_task

    @property
    def duration(self):
        return sum([d.duration for d in self.data])


class ParallelTaskCollection(AbstractTaskCollection):
    coll_type = 'parallel'
    def __repr__(self):
        return "ParallelTaskList <" + str(self) + ">"

    def __str__(self):
        if self.title is not None:
            return self.title
        else:
            return "(" + " / ".join([str(d) for d in self.data]) + ")"

    def plan(self, end=None, next_task=None):
        end = super().plan_end(end)
        for d in reversed(self.data):
            # all plan items must have same end date as task list (executed in parallel)
            _, t = d.plan(end, next_task=next_task)
        return self.start, t

    @property
    def duration(self):
        return max([d.duration for d in self.data])


def task_collection(plan_items, title=None, deadline=None, coll_type='serial'):
    coll = {'serial': SerialTaskCollection, 'parallel': ParallelTaskCollection}[coll_type](plan_items)
    coll.deadline = deadline
    coll.title = title
    return coll


serial = functools.partial(task_collection, coll_type='serial')
parallel = functools.partial(task_collection, coll_type='parallel')


def milestone(duration, title=None, resources=None):
    t = Task(duration, title, resources)
    t.coll_type = 'milestone'
    return t


def project(task_collection, deadline, title, slack=0):
    return serial([task_collection, milestone(slack, "Slack")], title=title, deadline=deadline)


def main():
    coll1 = serial([Task(1, "T1", resources=["piet", "klaas"]), Task(1, "T2"), Task(2, "T3")])

    coll2 = parallel([Task(1, "T4"), Task(2, "T5")])

    coll3 = serial([coll2, Task(1, "T6")])

    coll4 = serial([Task(1, "T7"), Task(1, "T8"), Task(3, "T9")])

    coll5 = parallel([Task(2, "T10"), Task(3, "T11")])

    coll6 = parallel([coll1, coll3, coll4, coll5])

    coll7 = serial([Task(1, "T12"), Task(3, "T13")])

    coll8 = parallel([coll7, Task(2, "T14")])

    collection = serial([coll6, coll8])
    p = project(collection, 11, "Ship development", slack=2)

    p.task("T2").progress = 0.5
    p.plan()

    plotter = MplPlotter()
    plotter.plot(p)
    plotter.show()


if __name__ == '__main__':
    main()
