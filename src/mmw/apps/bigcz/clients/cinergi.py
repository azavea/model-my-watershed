# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import requests
import dateutil.parser

from rest_framework.exceptions import ValidationError
from apps.bigcz.models import Resource, ResourceList, BBox


CATALOG_NAME = 'cinergi'
GEOPORTAL_URL = 'http://cinergi.sdsc.edu/geoportal/rest/find/document'


def parse_url(item):
    """
    Return "details" URL or first link if not found.
    """
    links = item['links']
    if links:
        for link in links:
            if link['type'] == 'details':
                return link['href']
        return links[0]['href']
    return None


def parse_date(value):
    try:
        # Some dates are 0-based?
        return dateutil.parser.parse(value)
    except ValueError:
        return None


def parse_record(item):
    return Resource(
        id=item['id'],
        title=item['title'],
        description=item['summary'],
        url=parse_url(item),
        created_at=None,
        updated_at=parse_date(item['updated']))


def prepare_bbox(value):
    box = BBox(value)
    return '{},{},{},{}'.format(box.xmin, box.ymin, box.xmax, box.ymax)


def prepare_date(value):
    return value.strftime('%Y-%m-%d')


def search(**kwargs):
    query = kwargs.get('query')
    to_date = kwargs.get('to_date')
    from_date = kwargs.get('from_date')
    bbox = kwargs.get('bbox')

    if not query:
        raise ValidationError({
            'error': 'Required argument: query'})

    params = {
        'searchText': query,
        'f': 'json',
    }

    if to_date:
        params.update({
            'before': prepare_date(to_date)
        })
    if from_date:
        params.update({
            'after': prepare_date(from_date)
        })
    if bbox:
        params.update({
            'bbox': prepare_bbox(bbox)
        })

    response = requests.get(GEOPORTAL_URL, params=params)

    data = response.json()
    if 'records' not in data:
        raise ValueError(data)

    results = data['records']
    count = data['totalResults']

    return ResourceList(
        catalog=CATALOG_NAME,
        count=count,
        results=[parse_record(item) for item in results])
