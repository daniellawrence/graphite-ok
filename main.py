#!/usr/bin/env python
from flask import Flask
from flask import request
from flask import render_template
import requests
from settings import *

app = Flask(__name__)

def _message(message, data, http_code=200):
    return render_template("results.html", message=message, data=data), http_code


def ok(message, data):
    return _message("OK: %s" % message, data, 200)


def warning(message, data):
    return _message("CRIT: %s" % message, data, WARNING_HTTP_RC)


def critical(message, data):
    return _message("CRIT: %s" % message, data, ERROR_HTTP_RC)


def build_graphite_url(target, within='15minutes'):
    base_render_url = 'http://%s/render?from=-%s&until=-&target=' % (GRAPHITE_SERVER, within)
    render_url = '%s%s&format=json' % (base_render_url, target)
    print render_url
    return render_url


def build_graph_url(target, within='15minutes'):
    base_render_url = 'http://%s/render?from=-%s&until=-&target=' % (GRAPHITE_SERVER, within)
    render_url = '%s%s&height=500&width=800&lineMode=staircase&template=plain' % (base_render_url, target)
    if 'asPercent' in render_url:
        render_url += '&yMin=0&yMax=100'
    print render_url
    return render_url


def grab_graphite_data(target):
    render_url = build_graphite_url(target)
    graph_url = build_graph_url(target)
    raw_graphite_data = requests.get(render_url)
    dp_list = []

    if raw_graphite_data.json() == []:
        return critical("No data found", {})

    all_graphite_data = raw_graphite_data.json()[0]

    for dp, ts in all_graphite_data['datapoints']:
        if dp is not None:
            dp_list.append(dp)
    dp_sum = sum(dp_list)
    dp_max = max(dp_list)
    dp_min = min(dp_list)
    avg_dp = sum(dp_list) / len(dp_list)

    return {
        'avg': avg_dp, 'list': dp_list, 'max': dp_max, 'min': dp_min,
        'render_url': render_url, 'graph_url': graph_url
        }


def helper():
    return render_template("base.html")


@app.route("/")
def index():
    args =  request.args
    print args
    if 'target' not in args:
        return helper()
    #return "ERROR: missing target"
    target = args['target']
    target_min = None
    target_max = None
    short_target = target.split('(')[-1].split(')')[0].split('%')[0]

    if 'min' in args and args['min'] != '':
        target_min = int(args['min'])
    if 'max' in args and args['max'] != '':
        target_max = int(args['max'])

    data = grab_graphite_data(target)

    if type(data) != type({}):
        return data

    data['target'] = target
    data['short_target'] = short_target
    data['target_min'] = target_min
    data['target_max'] = target_max

    if target_min:
        data['graph_url'] = data['graph_url'] + '&target=threshold(%s, "min", "yellow")' % target_min
        desc = "%s should be less than %s" % (short_target, target_min)
        data['desc'] = desc

    if target_max:
        desc = "%s should be greater than %s" % (short_target, target_max)
        data['desc'] = desc
        data['graph_url'] = data['graph_url'] + '&target=threshold(%s, "max", "red")' % target_max

    if target_min and target_max:
        desc = "%s should be between %s and %s" % (short_target, target_min, target_max)
        data['desc'] = desc

    data_avg = data['avg']

    if target_min and data_avg < target_min:
        p_under = (target_min / data_avg) * 100 - 100
        data['p_under'] = p_under
        return critical("%.2f less than %s" % (data_avg, target_min), data)

    if target_max and data_avg > target_max:
        p_over = (target_max / data_avg) * 100
        data['p_over'] = p_over
        return critical("%.2f greater than %s" % (data_avg, target_max), data)

    if target_min and target_max:
        return ok("%.2f is within: %s-%s" % (data_avg, target_min, target_max), data)

    if target_min:
        return ok("%.2f is greater than min %s" % (data_avg, target_min), data)

    if target_max:
        return ok("%.2f is less than max %s" % (data_avg, target_max), data)

    return ok("%.2f" % data_avg, data)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
