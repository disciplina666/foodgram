from django.core.exceptions import ValidationError


def validate_username(value):
    if value == 'me':
        raise ValidationError(
            'Имя пользователя "me" недопустимо.',
            params={'value': value},
        )

    invalid_chars = [
        char for char in value
        if not char.isalnum() and char not in '@.+-_'
    ]
    if invalid_chars:
        invalid_chars_str = ', '.join(invalid_chars)
        error_message = (
            'Имя пользователя содержит недопустимые символы: '
            f'{invalid_chars_str}.'
        )
        raise ValidationError(
            error_message,
            params={'value': value},
        )
