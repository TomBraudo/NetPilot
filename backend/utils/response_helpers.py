def success(message="", data=None):
    return {
        "success": True,
        "message": message,
        "data": {} if data is None else data
    }

def error(message="", status_code=400):
    return {
        "success": False,
        "message": message,
        "data": {}
    }
