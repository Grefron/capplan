from matplotlib import pyplot as plt, patches as mpatches


class PlotterBase:
    def plot(self, coll, x1=0, y1=0, x2=100, y2=100, task_list_progress=True, scaled=False):
        # TODO: Fix scaled version (must have a  reference time)
        if coll.activity_type == 'milestone':
            c, f, z = 'red', True, 1
        else:
            c, f, z = 'k', False, 2
        self.rect(x1=x1, y1=y1, x2=x2, y2=y2, fill=f, zorder=z, color=c)

        padding = 1
        if task_list_progress:
            p = 2 * padding
        else:
            p = 0

        if coll.activity_type in ['serial', 'project']:
            ddx = (x2 - x1) / len(coll)
            dx1 = 0
            for i, d in enumerate(coll):
                if scaled:
                    ddx += (x2 - x1) * d.duration / coll.duration
                self.plot(d, x1=x1 + dx1, y1=y1 + p, x2=x1 + dx1 + ddx, y2=y2)
                dx1 += ddx
        elif coll.activity_type == 'parallel':
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

        if task_list_progress and coll.activity_type is not 'task':
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
        # self.figure.show()
        plt.show()
