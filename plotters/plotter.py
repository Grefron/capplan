from matplotlib import pyplot as plt, patches as mpatches


class PlotterBase:
    def __init__(self):
        self.timelines = []

    def clear(self):
        self.timelines = []

    def plot_project(self, project):
        x1, x2 = project.start, project.end
        if len(self.timelines) == 0:
            self.timelines.append([project])
            return 0
        for i, projects in enumerate(self.timelines):
            overlap = False
            for p in projects:
                if p.start < project.start < p.end or p.start < project.end < p.end:
                    overlap = True
            if not overlap:
                return i
        self.timelines.append([project])
        return len(self.timelines) - 1

    def plot(self, coll, x1=0, y1=0, x2=100, y2=None, progressbar=True, scaled=True, padding=None):
        if y2 is None:
            y2 = x2 - x1
        if padding is None:
            padding = (0.01 * (x2 - x1), 0.03 * (y2 - y1))
        h_padding, v_padding = padding

        if coll.activity_type == 'project':
            self.text(x=(x1 + x2) / 2, y=y2 + v_padding / 2, caption=str(coll.title), ha='center', fontsize=10,
                      color='k', weight='bold')
        if coll.activity_type == 'milestone':
            self.rect(x1=x1, y1=y1, x2=x2, y2=y2, fill=True, zorder=1, color='red')
        else:
            self.rect(x1=x1, y1=y1, x2=x2, y2=y2, fill=False, zorder=2, color='k')

        p = v_padding if progressbar else 0

        if coll.activity_type in ['serial', 'project']:
            if scaled:
                for d in coll:
                    self.plot(d, x1=d.start, y1=y1 + p, x2=d.end, y2=y2, scaled=scaled, padding=padding)
            else:
                offset = 0
                width = (x2 - x1) / len(coll)
                for i, d in enumerate(coll):
                    self.plot(d, x1=x1 + offset, y1=y1 + p, x2=x1 + offset + width, y2=y2, scaled=scaled,
                              padding=padding)
                    offset += width
        elif coll.activity_type == 'parallel':
            dy = (y2 - y1 - p) / len(coll)
            if scaled:
                for i, d in enumerate(coll):
                    self.plot(d, x1=d.start, y1=y1 + i * dy + p, x2=x2, y2=y1 + (i + 1) * dy + p, scaled=scaled,
                              padding=padding)
            else:
                for i, d in enumerate(coll):
                    self.plot(d, x1=x1, y1=y1 + i * dy + p, x2=x2, y2=y1 + (i + 1) * dy + p, scaled=scaled,
                              padding=padding)
        else:  # assume task
            self.draw_task(coll, x1, y1, x2, y2, padding)

        if progressbar and coll.activity_type is not 'task':
            self.draw_progressbar(coll, x1, y1, x2, padding)

    def draw_progressbar(self, coll, x1, y1, x2, padding):
        h_padding, v_padding = padding
        y2 = y1 + v_padding
        self.rect(x1=x1, y1=y1, x2=x2, y2=y2, color='k', fill=False)
        self.rect(x1=x1, y1=y1, x2=x1 + (coll.progress * (x2 - x1)), y2=y2,
                  color='grey', zorder=1, fill=True)
        self.text(x=(x1 + x2) / 2, y=y1 + v_padding / 5,
                  caption=str(coll.duration), color='k', fontsize=9, zorder=10, ha='center')
        self.text(x=x1 + h_padding, y=y1 + v_padding / 5,
                  caption=str(coll.start), color='r', fontsize=9, zorder=10, ha='left')
        # task collection end
        self.text(x=x2 - h_padding, y=y1 + v_padding / 5, caption=str(coll.end),
                  color='b', fontsize=9, zorder=10, horizontalalignment='right')

    def draw_task(self, coll, x1, y1, x2, y2, padding):
        h_padding, v_padding = padding
        self.rect(x1=x1, y1=y1, x2=x2, y2=y2, color='lightblue', zorder=0, fill=True)
        self.rect(x1=x1, y1=y1, x2=x1 + (coll.progress * (x2 - x1)), y2=y2,
                  color='blue', zorder=1, fill=True)
        self.text(x=(x1 + x2) / 2, y=(y1 + y2) / 2,
                  caption=str(coll) + "(" + str(coll.duration) + ")", color='k', fontsize=10, zorder=10,
                  ha='center')
        self.text(x=(x1 + x2) / 2, y=y1 + h_padding,
                  caption=", ".join(coll.resources), color='k', fontsize=8, zorder=10, ha='center')
        self.text(x=(x1 + x2) / 2, y=y2 - 2 * h_padding,
                  caption="@" + str(coll.progress * 100) + "%", fontsize=9, zorder=10, ha='center')
        if coll.end is not None:
            self.text(x=x1 + h_padding, y=(y1 + y2) / 2,
                      caption=str(coll.start), color='r', fontsize=9, zorder=10, ha='left')
            self.text(x=x2 - h_padding, y=(y1 + y2) / 2,
                      caption=str(coll.end), color='b', fontsize=9, zorder=10, horizontalalignment='right')


class MplPlotter(PlotterBase):
    def __init__(self, width=10, height=8):
        super().__init__()
        self.figure = plt.figure(figsize=(width, height))
        self.ax = self.figure.add_subplot(111)
        self.figure.tight_layout()
        self.ax.axis(xmin=0, xmax=100, ymin=0, ymax=100)
        self.timeline_height = 10

    def clear(self):
        super().__init__()
        self.ax.clear()

    def plot_project(self, project):
        timeline = super().plot_project(project)
        y1 = 1.025 * timeline * self.timeline_height
        y2 = y1 + 0.95 * self.timeline_height
        self.plot(project, x1=project.start, y1=y1, x2=project.end, y2=y2, scaled=True)
        self.ax.autoscale()
        self.figure.tight_layout()

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
        weight = data.get('weight', 'normal')
        horizontalalignment = data.get('horizontalalignment', 'left')
        horizontalalignment = data.get('ha', horizontalalignment)
        zorder = data.get('zorder', 10)
        self.ax.text(x, y, caption, color=color, fontsize=fontsize,
                     zorder=zorder, horizontalalignment=horizontalalignment,
                     weight=weight)

    def show(self):
        # self.figure.show()
        plt.show()
