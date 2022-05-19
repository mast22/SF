from rest_framework.fields import ImageField as drf_ImageField, FileField as drf_FileField


class DRFYasgFileFieldRequiredFixMixin():
    """ Фикс drf-yasg, который отображал ImageField как  """
    class Meta:
        swagger_schema_fields = {
            'type': 'file',
            'read_only': False,
            'description': 'URL string when accessed or multipart file when created'
        }


class ImageField(drf_ImageField):
    pass


# class ImageField(drf_ImageField, DRFYasgFileFieldRequiredFixMixin):
#     pass


class FileField(drf_FileField, DRFYasgFileFieldRequiredFixMixin):
    pass
