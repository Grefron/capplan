#!flask/bin/python
from flask import Flask, abort
from flask_restplus import Api, Resource, reqparse
from serializer import deserialize, serialize
from tinydb import TinyDB, Query

from capplan import todo_list, resource_list

db = TinyDB('db.json')
app = Flask(__name__)
api = Api(app)

root_uri = '/capplan/api/v1.0/'


def get_projects(finished=False):
    projects = db.search((Query().activity_type == 'project') & (Query().finished == finished))
    return projects


def get_project_by_id(id):
    projects = db.search(
        (Query().activity_type == 'project') & (Query().metadata.id == id))
    if len(projects) > 0:
        return projects[0]
    else:
        return None


@api.route(root_uri + 'projects')
class AllProjects(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('finished', type=int,
                            help='Filter for (un)finished projects, 0=only unfinished projects. Defaults to 0')
        args = parser.parse_args()
        return {'projects': get_projects(finished=bool(args.get('finished', 0)))}


@api.route(root_uri + 'projects/<int:id>')
class ProjectById(Resource):
    def get(self, id):
        p = get_project_by_id(id)
        if p is not None:
            return {'project': p}
        else:
            abort(404)


@api.route(root_uri + 'resources')
class AllResources(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('finished', type=int,
                            help='Filter for (un)finished projects, 0=only unfinished projects. Defaults to 0')
        args = parser.parse_args()
        projects = [deserialize(p) for p in get_projects(finished=bool(args.get('finished', 0)))]
        return {'resources': resource_list(projects)}


@api.route(root_uri + 'todo/<resource>')
class TodoByResource(Resource):
    def get(self, resource):
        projects = [deserialize(p) for p in get_projects(finished=False)]
        tl = todo_list(projects, resources=[resource])
        return {'todo': [serialize(task) for task in tl]}


if __name__ == '__main__':
    app.run(debug=True)
