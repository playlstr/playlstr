from playlstr.models import PlaylstrUser
from django.utils import timezone


def link_client_code(link_code: str, client_id: str):
    """
    Link client client_id to link code link_code
    :param link_code: a valid link code
    :param client_id: a valid 20 character client id
    :raises ValueError if code or client_id is invalid
    """
    if len(client_id) != 20:
        raise ValueError('Invalid client ID')
    user = PlaylstrUser.objects.filter(link_code=link_code).first()
    if user is None:
        raise ValueError('No user matching link code')
    if (timezone.now() - user.link_code_generated).total_seconds() > 120000:
        raise ValueError('Code expired')
    user.linked_clients.append(client_id)
    user.save()
