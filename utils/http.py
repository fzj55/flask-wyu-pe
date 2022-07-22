import json

from flask import Response




def render_json(data,code=0,msg='成功'):
    result={
        'data':data,
        'code':code,
        'msg':msg
    }

    #if app.config.DEBUG:
    json_str=json.dumps(result, indent=4, ensure_ascii=False, sort_keys=True)
    #else:
     #   json_str =json.dumps(result,separators=(',',':'),ensure_ascii=False)
    return Response(json_str)