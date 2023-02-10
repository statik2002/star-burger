from http.client import HTTPResponse


def index(request):
    return HTTPResponse('Addresses')
