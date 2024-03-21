from djproxy.views import HttpProxy


class NodeRedProxy(HttpProxy):
    base_url = "http://localhost:1880"
