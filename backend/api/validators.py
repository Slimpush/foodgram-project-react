import re

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_username(value):
    invalid_symbols = re.findall(settings.REGEX_USERNAME, value)
    if invalid_symbols:
        raise ValidationError(
            'Недопустимые символы в имени пользователя: {}'.format(
                ', '.join(set(invalid_symbols))
            )
        )

    if value in settings.INVALID_NAMES:
        raise ValidationError(
            'Использовать "{}" в качестве имени запрещено.'.format(value)
        )
