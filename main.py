#!/usr/bin/env python
from flask import Flask
from flask import request
import requests

from settings import *

app = Flask(__name__)

def _message(message, http_code=200):
    return "%s" % message, http_code
    
def ok(message):
    return _message("OK: %s" % message, 200)
    
def warning(message):
    return _message("CRIT: %s" % message, WARNING_HTTP_RC)
    
def critical(message):
    return _message("CRIT: %s" % message, ERROR_HTTP_RC)

def build_graphite_url(target, within='15minutes'):
    base_render_url = 'http://%s/render?from=-%s&until=-&target=' % (GRAPHITE_SERVER, within)
    render_url = '%s%s&format=json' % (base_render_url, target)
    return render_url

def grab_graphite_data(target):
    render_url = build_graphite_url(target)
    all_graphite_data = requests.get(render_url).json()[0]
    dp_list = []
    for dp, ts in all_graphite_data['datapoints']:
        if dp:
            dp_list.append(dp)
    dp_sum = sum(dp_list)
    dp_max = max(dp_list)
    dp_min = min(dp_list)
    avg_dp = sum(dp_list) / len(dp_list)
    return {'avg': avg_dp, 'list': dp_list, 'max': dp_max, 'min': dp_min}

@app.route("/")
def index():
    args =  request.args
    if 'target' not in args:
        return "ERROR: missing target"
    target = args['target']
    target_min = None
    target_max = None
    if 'min' in args:
        target_min = int(args['min'])
    if 'max' in args:
        target_max = int(args['max'])
        
    data = grab_graphite_data(target)
    data_avg = data['avg']
    if target_min and data_avg < target_min:
        return critical("%.2f less than %s" % (data_avg, target_min))
        
    if target_max and data_avg > target_max:
        return critical("%.2f greater than %s" % (data_avg, target_max))

    if target_min and target_max:
        return ok("%.2f is within: %s-%s" % (data_avg, target_min, target_max))
        
    if target_min:
        return ok("%.2f is greater than min %s" % (data_avg, target_min))
        
    if target_max:
        return ok("%.2f is less than max %s" % (data_avg, target_max))

    return ok("%.2f" % data_avg)

if __name__ == "__main__":
    app.run(debug=True)
