import json
from django.http import JsonResponse


def safe_json(request):

    try:

        body = request.body.decode(
            "utf-8",
            errors="ignore"
        ).strip()

        if not body:

            return {
                "_error": "empty request body"
            }

        parsed = json.loads(body)

        if not isinstance(parsed, dict):

            return {
                "_error": "JSON body must be object"
            }

        return parsed

    except Exception as e:

        return {
            "_error": str(e)
        }


def api_error(
    message="Error",
    status=400,
    extra=None
):

    data = {

        "success": False,
        "error": message

    }

    if extra is not None:

        data["extra"] = extra

    return JsonResponse(
        data,
        status=status
    )