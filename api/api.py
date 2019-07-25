import flask
import flask_restful
import werkzeug.routing
import routes
# from getpass import getpass

# Defining int_list for batch GET requests


class IntListConverter(werkzeug.routing.BaseConverter):
    regex = r'\d+(?:,\d+)*,?'

    def to_python(self, value):
        return [int(i) for i in value.split(',')]

    def to_url(self, value):
        return ','.join(str(i) for i in value)


# Initializing app and api

app = flask.Flask(__name__)
app.url_map.converters['int_list'] = IntListConverter
api = flask_restful.Api(app)

# Adding resources to api
api.add_resource(routes.InterviewAll, '/interviews/all')
api.add_resource(routes.InterviewAllText, '/interviews/all/text')
api.add_resource(routes.InterviewAllQuestions, '/interviews/all/questions')
api.add_resource(routes.InterviewAllAnswers, '/interviews/all/answers')
api.add_resource(routes.InterviewAny, '/interviews/<int_list:ids>')
api.add_resource(routes.InterviewAnyText, '/interviews/<int_list:ids>/text')
api.add_resource(routes.InterviewAnyQuestions,
                 '/interviews/<int_list:ids>/questions')
api.add_resource(routes.InterviewAnyAnswers,
                 '/interviews/<int_list:ids>/answers')

# Testing authentication

# Main script
if __name__ == "__main__":
    app.run(debug=True)