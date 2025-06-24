def success(message="", data=None, status_code=200):
    return {
        "success": True,
        "message": message,
        "data": {} if data is None else data,
        "status_code": status_code
    }

def error(message="", status_code=400):
    return {
        "success": False,
        "message": message,
        "data": {},
        "status_code": status_code
    }
