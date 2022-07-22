from itsdangerous import URLSafeTimedSerializer as utsr
import base64
import settings
from exts import cache


# session 服务器 crsf攻击
# cookies 浏览器
# token 每次登录验证的令牌
class Token:
    def __init__(self, security_key):
        self.security_key = security_key
        self.salt = base64.encodestring(security_key.encode('utf8'))

    # 做签名
    def generate_validte_token(self, uid):
        serializer = utsr(self.security_key)
        token = serializer.dumps(uid, salt=self.salt)
        cache.set(':'.join(['token', uid]), token, timeout=126144000)
        return token

    # 反向签名
    def confirm_validate_token(self, token, uid):
        serializer = utsr(self.security_key)
        id = serializer.loads(token, salt=self.salt)
        if id != uid:
            raise ValueError('非法尝试')

        t = cache.get(':'.join(['token', uid]))
        if t == token:
            return id
        else:
            raise ValueError('token过期')

    def remove_validate_token(self, token, uid):
        serlizer = utsr(self.security_key)
        id = serlizer.loads(token, salt=self.salt)
        if id != uid:
            raise ValueError('非法尝试')
        t = cache.get(':'.join(['token', uid]))
        if t == token:
            return cache.delete(uid)
        else:
            raise ValueError('token过期')


# 实例化token传入秘钥
token_confirm = Token(settings.Config.SECRET_KEY)  # 定义全局变量
