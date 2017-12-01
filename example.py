from capplan import Serial, Task, Parallel, Project, deserialize, serialize


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
    p = Project(collection, 11, "Ship development", slack=2)
    return p


def main():
    from plotters.plotter import MplPlotter
    p1 = example_project()
    p1.task("T2").progress = 0.5

    p2 = deserialize(serialize(p1))

    p2.plan()
    plotter = MplPlotter()
    plotter.plot_project(p2)
    plotter.show()


if __name__ == '__main__':
    main()
