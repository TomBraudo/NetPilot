def success(message="", data=None):
    return {
        "success": True,
        "message": message,
        "data": data or {}
    }

def error(message="", status_code=400):
    return {
        "success": False,
        "message": message,
        "data": {}
    }, status_code
