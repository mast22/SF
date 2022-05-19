from rest_framework.pagination import PageNumberPagination as drf_PageNumberPagination
from rest_framework_json_api.pagination import JsonApiPageNumberPagination as drf_JsonApiPageNumberPagination
from rest_framework.views import Response
from collections import OrderedDict


class PageNumberPagination(drf_PageNumberPagination):
    max_page_size = 1000


class JsonApiPageNumberPagination(drf_JsonApiPageNumberPagination):
    max_page_size = 1000


    def get_paginated_response(self, data, aggregated_stats=None):
        next = None
        previous = None

        if self.page.has_next():
            next = self.page.next_page_number()
        if self.page.has_previous():
            previous = self.page.previous_page_number()

        meta = OrderedDict([
            ('pagination', OrderedDict([
                ('page', self.page.number),
                ('pages', self.page.paginator.num_pages),
                ('count', self.page.paginator.count),
            ])),
        ])

        if aggregated_stats:
            meta['aggregated_stats'] = aggregated_stats

        return Response({
            'results': data,
            'meta': meta,
            'links': OrderedDict([
                ('first', self.build_link(1)),
                ('last', self.build_link(self.page.paginator.num_pages)),
                ('next', self.build_link(next)),
                ('prev', self.build_link(previous))
            ])
        })
