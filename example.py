from capplan.capplan import Serial, Task, Parallel, Project, todo_list
from capplan.serializer import serialize, deserialize


def example_project():
    coll1 = Serial([Task(1, "T1", resources=["piet", "klaas"]), Task(1, "T2"), Task(2, "T3")])
    coll2 = Parallel([Task(1, "T4"), Task(2, "T5")])
    coll3 = Serial([coll2, Task(1, "T6")])
    coll4 = Serial([Task(1, "T7"), Task(1, "T8"), Task(3, "T9")])
    coll5 = Parallel([Task(2, "T10"), Task(3, "T11")])
    coll6 = Parallel([coll1, coll3, coll4, coll5])
    coll7 = Serial([Task(1, "T12"), Task(3, "T13")])
    coll8 = Parallel([coll7, Task(2, "T14")])
    collection = Serial([coll6, coll8])
    p = Project(collection, 11, "Example project", slack=2)
    return p


def main():
    from plotters.plotter import MplPlotter
    import json
    import pprint

    from tinydb import TinyDB, Query
    db = TinyDB('.\\capplan\\db.json')

    pl = []

    p1 = example_project()
    p1.metadata = {'id': 123}
    p1.task("T2").progress = 0.5
    p1.plan()

    db.insert(serialize(p1))
    project_query = Query()
    p3 = deserialize(db.search(project_query.metadata.id == 123)[0])
    p3.plan()

    # (de)serialize from/to dict
    p2 = deserialize(serialize(p1))

    # print(p3)
    # pprint.pprint(collection.find()[1])

    pl.append(p1)
    pl.append(p2)

    p2.shift_deadline(15)
    p2.plan()

    # use/store data
    json.dumps(serialize(p2))
    pprint.pprint(serialize(p2))

    # show structure visually
    plotter = MplPlotter()
    plotter.plot_project(p2)
    plotter.plot_project(p3)
    plotter.show()

    tl = todo_list([p1, p2])
    serialize(tl)


if __name__ == '__main__':
    main()
