import collections
import functools

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt


# TODO: Add TaskCollection.append / TaskCollection.prepend / TaskCollection.parallel


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


class PlotterBase:
    def plot(self, coll, x1=0, y1=0, x2=100, y2=100, task_list_progress=True, scaled=False):
        # TODO: Fix scaled version (must have a  reference time)
        if isinstance(coll, SerialTaskCollection):
            coll_type = 'serial'
        elif isinstance(coll, ParallelTaskCollection):
            coll_type = 'parallel'
        else:
            coll_type = 'task'

        self.rect(x1=x1, y1=y1, x2=x2, y2=y2, fill=False, zorder=2)

        padding = 1
        if task_list_progress:
            p = 2 * padding
        else:
            p = 0

        if coll_type == 'serial':
            ddx = (x2 - x1) / len(coll)
            dx1 = 0
            for i, d in enumerate(coll):
                if scaled:
                    ddx += (x2 - x1) * d.duration / coll.duration
                self.plot(d, x1=x1 + dx1, y1=y1 + p, x2=x1 + dx1 + ddx, y2=y2)
                dx1 += ddx
        elif coll_type == 'parallel':
            dy = (y2 - y1 - p) / len(coll)
            for i, d in enumerate(coll):
                self.plot(d, x1=x1, y1=y1 + i * dy + p, x2=x2, y2=y1 + (i + 1) * dy + p)
        else:  # assume task
            self.rect(x1=x1, y1=y1, x2=x1 + (coll.progress * (x2 - x1)), y2=y2,
                      color='lightgrey', zorder=1, fill=True)
            self.text(x=(x1 + x2) / 2, y=(y1 + y2) / 2,
                      caption=str(coll) + "(" + str(coll.duration) + ")", color='k', fontsize=10, zorder=10,
                      ha='center')
            self.text(x=(x1 + x2) / 2, y=y1 + padding,
                      caption=", ".join(coll.resources), color='k', fontsize=8, zorder=10, ha='center')
            self.text(x=(x1 + x2) / 2, y=y2 - 2 * padding,
                      caption="@" + str(coll.progress * 100) + "%", fontsize=9, zorder=10, ha='center')
            if coll.end is not None:
                self.text(x=x1 + padding, y=(y1 + y2) / 2,
                          caption=str(coll.start), color='r', fontsize=9, zorder=10, ha='left')
                self.text(x=x2 - padding, y=(y1 + y2) / 2,
                          caption=str(coll.end), color='b', fontsize=9, zorder=10, horizontalalignment='right')
                self.text(x=(x2 + x1) / 2, y=(y2 + y1) / 2 + 2 * padding,
                          caption=str(coll.next_task), color='k', fontsize=9, zorder=10, ha='center')

        if task_list_progress and coll_type is not 'task':
            y2 = y1 + p
            self.rect(x1=x1, y1=y1, x2=x1 + (coll.progress * (x2 - x1)), y2=y2,
                      color='grey', zorder=1, fill=True)
            self.text(x=(x1 + x2) / 2, y=y1 + p / 5,
                      caption=str(coll.duration), color='k', fontsize=9, zorder=10, ha='center')
            self.text(x=x1 + padding, y=y1 + p / 5,
                      caption=str(coll.start), color='r', fontsize=9, zorder=10, ha='left')
            # task collection end
            self.text(x=x2 - padding, y=y1 + p / 5, caption=str(coll.end),
                      color='b', fontsize=9, zorder=10, horizontalalignment='right')


class MplPlotter(PlotterBase):
    def __init__(self, width=10, height=8):
        self.figure = plt.figure(figsize=(width, height))
        self.ax = self.figure.add_subplot(111)
        self.figure.tight_layout()

        self.ax.axis(xmin=0, xmax=100, ymin=0, ymax=100)

    def clear(self):
        self.ax.clear()

    def rect(self, **data):
        x1, y1, x2, y2 = data['x1'], data['y1'], data['x2'], data['y2']
        color = data.get('color', 'k')
        fill = data.get('fill', False)
        zorder = data.get('zorder', 11)
        self.ax.add_patch(mpatches.Rectangle((x1, y1), (x2 - x1), (y2 - y1),
                                             color=color, fill=fill, zorder=zorder))

    def text(self, **data):
        x, y = data['x'], data['y']
        caption = data['caption']
        color = data.get('color', 'b')
        fontsize = data.get('fontsize', 10)
        horizontalalignment = data.get('horizontalalignment', 'left')
        horizontalalignment = data.get('ha', horizontalalignment)
        zorder = data.get('zorder', 10)
        self.ax.text(x, y, caption, color=color, fontsize=fontsize,
                     zorder=zorder, horizontalalignment=horizontalalignment)

    def show(self):
        self.figure.show()

coll1 = serial([Task(1, "T1", resources=["piet", "klaas"]), Task(1, "T2"), Task(2, "T3")])

coll2 = parallel([Task(1, "T4"), Task(2, "T5")])

coll3 = serial([coll2, Task(1, "T6")])

coll4 = serial([Task(1, "T7"), Task(1, "T8"), Task(3, "T9")])

coll5 = parallel([Task(2, "T10"), Task(3, "T11")])

coll6 = parallel([coll1, coll3, coll4, coll5])

coll7 = serial([Task(1, "T12"), Task(3, "T13")])

coll8 = parallel([coll7, Task(2, "T14")])

project = serial([coll6, coll8, Task(1, "T15")], deadline=10)

project.task("T2").progress = 0.5
project.plan()

plotter = MplPlotter()
plotter.plot(project)
plt.show()

