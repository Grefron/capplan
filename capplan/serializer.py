from capplan import TaskCollection, Task, Serial, Parallel, Project, Milestone


def serialize(activity):
    def serialize_task(task):
        ser = {'title': task.title,
               'duration': task.duration,
               'resources': task.resources,
               'end': task.end,
               'progress': task.progress,
               'activity_type': task.activity_type,
               'metadata': task.metadata}
        if task.next_task is not None:
            ser['next_task'] = str(task.next_task)
        if task.start is not None:
            ser['start'] = task.start
        return ser

    def serialize_collection(collection):
        ser = {'title': collection.title,
               'end': collection.end,
               'deadline': collection.deadline,
               'duration': collection.duration,
               'activity_type': collection.activity_type,
               'activities': [serialize(t) for t in collection.data],
               'metadata': collection.metadata}
        if isinstance(collection, Project):
            ser['finished'] = collection.finished
        return ser

    if isinstance(activity, TaskCollection):
        return serialize_collection(activity)
    elif isinstance(activity, Task):
        return serialize_task(activity)
    elif isinstance(activity, dict):  # assume list of tasks
        return [serialize_task(a) for a in activity]


def deserialize(data):
    def deserialize_task(data, cls):
        t = cls(duration=data['duration'], title=data['title'], resources=data['resources'], progress=data['progress'])
        t.end = data['end']
        t.next_task = data.get('next_task', None)
        t.metadata = data.get('metadata', {})
        return t

    def deserialize_collection(data, cls):
        c = cls([deserialize(d) for d in data['activities']], title=data['title'], end=data['end'],
                deadline=data['deadline'])
        c.metadata = data.get('metadata', {})
        return c

    def deserialize_project(data, cls):
        p = cls(initlist=[deserialize(d) for d in data['activities'][0:-1]], title=data['title'],
                deadline=data['deadline'], slack=data['activities'][-1]['duration'])
        p.metadata = data.get('metadata', {})
        p.finished = data.get('finished', False)
        return p

    if isinstance(data, list):  # assume list of tasks
        return [deserialize_task(d) for d in data]

    coll_types = {'serial': Serial, 'parallel': Parallel}
    project_types = {'project': Project}
    task_types = {'task': Task, 'milestone': Milestone}

    at = data['activity_type']

    if at in coll_types.keys():
        return deserialize_collection(data, coll_types[at])
    elif at in task_types.keys():
        return deserialize_task(data, task_types[at])
    elif at in project_types.keys():
        return deserialize_project(data, project_types[at])
    else:
        raise KeyError('cannot find deserializer')
