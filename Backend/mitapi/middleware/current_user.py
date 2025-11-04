from threading import local

from django.utils.deprecation import MiddlewareMixin

_user = local()


class CurrentUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _user.value = request.user


def get_current_user():
    try:
        return _user.value
    except AttributeError:
        return None

def get_current_user_groups():
    from django.contrib.auth.models import Group
    try:
        query_set = Group.objects.filter(user = _user.value)
        return query_set.values_list('name', flat = True)
    except AttributeError:
        return None

def get_compCode():
    # compCode = 'mps'
    compCode = 'mpam'
    return compCode
