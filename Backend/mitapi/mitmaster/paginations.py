from rest_framework import pagination
from rest_framework.response import Response
from collections import OrderedDict


class CustomPagination(pagination.PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 50
    page_query_param = 'p'

    def get_paginated_response(self, data):
        response = Response(data)
        response['found_data'] = self.page.paginator.count
        response['page_number'] = self.page.number
        response['page_range'] = self.page.paginator.page_range
        response['page_next'] = self.get_next_link()
        response['page_previous'] = self.get_previous_link()
        return response
