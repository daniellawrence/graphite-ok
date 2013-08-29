# The local graphite server
GRAPHITE_SERVER = 'graphite'

# http return code in the event of a error/critical
ERROR_HTTP_RC = 506

# http return code in the event of a warning
WARNING_HTTP_RC = 200

try:
    from local_settings import *
except ImportError:
    pass
