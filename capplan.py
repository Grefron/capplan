import collections


class PlannerError(Exception):
    pass


class ActivityMixin:
    @property
    def start(self):
        # latest start date for this task, no slack in this task allows
        if self.end is None:
            return None
        return self.end - self.duration


class Task(ActivityMixin):
    activity_type = 'task'

    def __init__(self, duration, title=None, resources=None, progress=0):
        if resources is None:
            resources = []
        self.title = title
        self.duration = duration
        self.resources = resources
        self.end = None  # absolute latest end date, no slack in this or later tasks allowed
        self.progress = progress
        self.next_task = None

    @property
    def duration(self):
        return self._duration * (1.0 - self.progress)

    @duration.setter
    def duration(self, value):
        self._duration = value

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
        self.next_task = next_task
        return self.start, self


class Milestone(Task):
    activity_type = 'milestone'


class TaskCollection(collections.UserList, ActivityMixin):
    activity_type = 'abstract'

    def __init__(self, initlist=None, title=None, end=None, deadline=None):
        super().__init__(initlist)
        self.title = title
        self.end = end
        self.deadline = deadline

    def __repr__(self):
        return self.__class__.__name__ + "<" + str(self) + ">"

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


class Serial(TaskCollection):
    activity_type = 'serial'

    def __str__(self):
        if self.title is not None:
            return self.title
        else:
            return "(" + " - ".join([str(d) for d in self.data]) + ")"

    def plan(self, end=None, next_task=None):
        end = super().plan_end(end)
        for d in reversed(self):
            # all plan items must have an end date equal to start date of next task (backwards planning)
            end, next_task = d.plan(end, next_task=next_task)
        return self.start, next_task

    @property
    def duration(self):
        return sum([d.duration for d in self.data])


class Parallel(TaskCollection):
    activity_type = 'parallel'

    def __str__(self):
        if self.title is not None:
            return self.title
        else:
            return "(" + " / ".join([str(d) for d in self.data]) + ")"

    def plan(self, end=None, next_task=None):
        end = super().plan_end(end)
        for d in reversed(self):
            # all plan items must have same end date as task list (executed in parallel)
            _, t = d.plan(end, next_task=next_task)
        return self.start, t

    @property
    def duration(self):
        return max([d.duration for d in self.data])


class Project(Serial):
    activity_type = 'project'

    def __init__(self, initlist=None, deadline=None, title=None, slack=0):
        super().__init__(initlist=initlist, deadline=deadline, title=title)
        self.data.append(Milestone(slack, "Milestone"))


def serialize(activity):
    def serialize_task(task):
        ser = {'title': task.title,
               'duration': task.duration,
               'resources': task.resources,
               'end': task.end,
               'progress': task.progress,
               'activity_type': task.activity_type}
        if task.next_task is not None:
            ser['next_task'] = str(task.next_task)
        if task.start is not None:
            ser['start'] = task.start
        return ser

    def serialize_collection(collection):
        ser = {'activities': [serialize(t) for t in collection.data],
               'title': collection.title,
               'end': collection.end,
               'deadline': collection.deadline,
               'duration': collection.duration,
               'activity_type': collection.activity_type}
        return ser

    if isinstance(activity, TaskCollection):  # in ['serial', 'parallel', 'project']:
        return serialize_collection(activity)
    elif isinstance(activity, Task):  # in ['task', 'milestone']:
        return serialize_task(activity)


def deserialize(data):
    def deserialize_task(data, cls):
        t = cls(duration=data['duration'], title=data['title'], resources=data['resources'], progress=data['progress'])
        t.end = data['end']
        t.next_task = data.get('next_task', None)
        return t

    def deserialize_collection(data, cls):
        return cls([deserialize(d) for d in data['activities']], title=data['title'], end=data['end'],
                   deadline=data['deadline'])

    def deserialize_project(data, cls):
        return cls(initlist=[deserialize(d) for d in data['activities'][0:-1]], title=data['title'],
                   deadline=data['deadline'], slack=data['activities'][-1]['duration'])

    coll_types = {'serial': Serial, 'parallel': Parallel}
    project_types = {'project': Project}
    task_types = {'task': Task, 'milestone': Milestone}

    at = data['activity_type']
    print(data['activity_type'])

    if at in coll_types.keys():
        return deserialize_collection(data, coll_types[at])
    elif at in task_types.keys():
        return deserialize_task(data, task_types[at])
    elif at in project_types.keys():
        return deserialize_project(data, project_types[at])
    else:
        raise KeyError('cannot find deserializer')
