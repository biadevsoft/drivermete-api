from django.conf import settings

from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
    page_size_query_param = 'per_page'
    max_page_size = 100

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paginator = None

    def get_paginated_response(self, data):
        self.paginator = self.page.paginator
        response = super().get_paginated_response(data)
        response.data['pagination'] = {
            'total_items': response.data.get('count', 0),
            'per_page': self.page_size,
            'current_page': self.page.number,
            'total_pages': self.paginator.num_pages,
        }
        return response
