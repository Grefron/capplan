import collections
import functools


class PlannerError(Exception):
    pass


class PlanItemMixin:
    @property
    def greenstart(self):
        # latest safe start date for this task, slack in this task allowed
        return self.end - self.duration - self.slack

    @property
    def redstart(self):
        # latest start date for this task, no slack in this task allows
        return self.end - self.duration


class Task(PlanItemMixin):
    def __init__(self, title, duration, resources=None, slack=0):
        if resources is None:
            resources = []
        self.title = title
        self.duration = duration
        self.resources = resources
        self.slack = slack
        self.end = None  # absolute latest end date, no slack in this or later tasks allowed

    def tasks(self, resources=None, sort=True):
        if resources is None:
            return [self]
        if len(set(self.resources) & set(resources)) > 0:
            return [self]
        else:
            return []

    def plan(self, end):
        # plan deadline for this task and return deadline for previous task
        self.end = end
        return self.redstart


class AbstractTaskList(collections.UserList, PlanItemMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = None
        self.end = None
        self.deadline = None
        
    def tasks(self, resources=None, sort=True):
        tasks = []
        for d in self.data:
            tasks += d.tasks(resources, sort)
        tasks = list(set(tasks))
        if sort:
            return tasks
        else:
            return tasks

    def plan(self, end=None):
        if end is None and self.deadline is None:
            raise PlannerError()

        if self.deadline is not None:
            end = self.deadline
        else:
            end = self.end
        return end

    @property
    def duration(self):
        raise NotImplementedError()    

    @property
    def slack(self):
        raise NotImplementedError()


class SerialTaskList(AbstractTaskList):
    def plan(self, end=None):
        end = super().plan(end)
        for d in reversed(self.data):
            # all plan items must have an end date equal to start date of next task (backwards planning)
            end = d.plan(end)
            
    @property
    def duration(self):
        return sum([d.duration for d in self.data])
        
    @property
    def slack(self):
        return sum([d.slack for d in self.data])


class ParallelTaskList(AbstractTaskList):
    def plan(self, end=None):
        end = super().plan(end)
        for d in reversed(self.data):
            # all plan items must have same end date as task list (executed in parallel)
            d.plan(end)

    @property
    def duration(self):
        return max([d.duration for d in self.data])

    @property
    def slack(self):
        return max([d.slack for d in self.data])
       

def task_list(plan_items, title=None, deadline=None, tl_type='serial'): 
    tl = {'serial': SerialTaskList, 'parallel': ParallelTaskList}[tl_type](plan_items)
    tl.deadline = deadline
    tl.title = title
    return tl

serial = functools.partial(task_list, tl_type='serial')
parallel = functools.partial(task_list, tl_type='parallel')

t1 = [Task("t11", 1, ['kees', 'piet']), Task("t12", 2, ['kees', 'karel'])]
t2 = [Task("t21", 3, ['piet']), Task("t22", 1, ["kees", "karel"])]

tl1 = serial(t1, title="tl1 - t11/t12", deadline=10)
tl1.plan()

tl2 = parallel(t2, title="t2 - t21/t22")

project = serial([tl1, tl2], title="test", deadline=5)
project.plan()

print(project.tasks(["piet"]))