from sys import argv, stderr
from datetime import datetime
from bson.son import SON

stderr.write('reading settings.py...')

def current_hour():
    """
    Return the current hour with the least significant
    time segments set to 0
    """
    now = datetime.now()
    y, m, d, h = (now.year, now.month, now.day, now.hour)
    return datetime(y, m, d, h, 0)


MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_USERNAME = ''
MONGO_PASSWORD = ''
stderr.write(str(argv))
if 'test' in argv:
    MONGO_DBNAME = 'testdb'
else:
    MONGO_DBNAME = 'arduinolog'

RESOURCE_METHODS = ['GET', 'POST', 'DELETE']
ITEM_METHODS = ['GET']

CACHE_CONTROL = 'max-age=20'
CACHE_EXPIRES = 20

timeseriesdata = {
    'item_title': 'snapshot',
    'additional_lookup': {
        'url': 'regex("[\w]+")',
        'field': 'name'
    },
    'datasource': {
        'default_sort': [('ts_hour', -1)]
    },
    'schema': {
        'name': {
            'type': 'string',
        },
        'ts_hour': {
            'type': 'datetime',
        },
        'values': {
            'type': 'list',
            'schema': {
                'type': 'float'
            },
        },
    }
}

eventdata = {
    'item_title': 'event',
    'additional_lookup': {
        'url': 'regex("[\w]+")',
        'field': 'name'
    },
    'datasource': {
        'default_sort': [('ts', -1)]
    },
    'schema': {
        'name': {
            'type': 'string',
        },
        'ts': {
            'type': 'datetime',
        },
        'value': {
            'type': 'float',
        },
    },
}

hour_stats = {
    'datasource': {
        'source': 'timeseriesdata',
        'aggregation': {
            'pipeline': [
                # {
                #     '$match': {
                #         'name': 'tempF'
                #     }
                # },
                {
                    '$match': {
                        'ts_hour': {
                            '$gte': current_hour()
                        }
                    }
                },
                {
                    '$unwind': '$values'
                },
                {
                    '$group': {
                        '_id': '$name',
                        'min': {
                            '$min': '$values'
                        },
                        'max': {
                            '$max': '$values'
                        },
                        'avg': {
                            '$avg': '$values'
                        }
                    }
                },
                {
                    '$sort': SON([("max", -1), ("_id", -1)])
                }
            ]
        }
    }
}

agg_test = {
    'datasource': {
        'source': 'timeseriesdata',
        'aggregation': {
            'pipeline': [
                {"$unwind": "$values"},
                {"$group": {"_id": "$values", "count": {"$sum":
                                                      "$field1"}}},
                {"$sort": SON([("count", -1), ("_id", -1)])}
            ],
        }
    }
}

DOMAIN = {
    'timeseriesdata': timeseriesdata,
    'eventdata': eventdata,
    'stats': hour_stats,
    'agg': agg_test,
}
