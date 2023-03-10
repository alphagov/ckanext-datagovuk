from flask import current_app, Response


def metrics():
    data, content_type = current_app._metrics.generate_metrics()
    return Response(data, mimetype=content_type)
