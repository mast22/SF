from rest_framework import serializers as s

# Инициализированное поле для использования в сваггере
# или в SerializerMethodField для сериализации данных
price_serializer_field = s.DecimalField(decimal_places=2, max_digits=10)