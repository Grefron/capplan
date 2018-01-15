#!flask/bin/python
from flask import Flask, abort
from flask_restplus import Api, Resource
from serializer import deserialize, serialize
from tinydb import TinyDB, Query

from capplan import todo_list, resource_list

db = TinyDB('db.json')
app = Flask(__name__)
api = Api(app)

root_uri = '/capplan/api/v1.0/'


def active_projects():
    projects = db.search((Query().activity_type == 'project') & (Query().finished == False))
    return projects


def active_project(id):
    projects = db.search(
        (Query().activity_type == 'project') & (Query().finished == False) & (Query().metadata.id == id))
    if len(projects) > 0:
        return projects[0]
    else:
        return None


@api.route(root_uri + 'projects')
class AllProjects(Resource):
    def get(self):
        return {'projects': active_projects()}


@api.route(root_uri + 'projects/<int:id>')
class ProjectById(Resource):
    def get(self, id):
        p = active_project(id)
        if p is not None:
            return {'project': p}
        else:
            abort(404)


@api.route(root_uri + 'resources')
class AllResources(Resource):
    def get(self):
        projects = [deserialize(p) for p in active_projects()]
        return {'resources': resource_list(projects)}


@api.route(root_uri + 'todo/<resource>')
class TodoByResource(Resource):
    def get(self, resource):
        projects = [deserialize(p) for p in active_projects()]
        tl = todo_list(projects, resources=[resource])
        return {'todo': [serialize(task) for task in tl]}


if __name__ == '__main__':
    app.run(debug=True)
