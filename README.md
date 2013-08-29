graphite-ok
===========

Easily check the status of a graphite metric via http return codes.

Installation
------------

```sh
git clone https://github.com/daniellawrence/graphite-ok
cd graphite-ok
pip install -r requirements.txt
python ./main.py
```

Examples:
---------

```sh
curl -v http://graphite:5000/\?target=asPercentage(metric1, metric2)&max=80
```
