import json
from flask import request, _request_ctx_stack, abort, session,  url_for
from functools import wraps
from jose import jwt
from urllib.request import Request, urlopen
from os import environ as env

AUTH0_DOMAIN = 'audacity-fsnd-sarbani.uk.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'capstone'
PAYLOAD_PERMISSIONS = 'permissions'

def auth_register(oauth):
    oauth.register(
        "auth0",
        client_id=env.get("AUTH0_CLIENT_ID"),
        client_secret=env.get("AUTH0_CLIENT_SECRET"), 
        authorize_url=f'https://{env.get("AUTH0_DOMAIN")}/authorize?audience=capstone',
        # response_type='response_type=token',
        client_kwargs={
            "scope": "openid profile email",
        },
        server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
    )


    # @app.route("/login")
    # def login():
    #     return oauth.auth0.authorize_redirect(
    #         redirect_uri=url_for("callback", _external=True)
    #     )


## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code
        print(error)
        print(status_code)
        abort(status_code)

## Auth Header

'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
def get_token_auth_header(session):
    print("inside get token auth header")
    token=session.get('user')['access_token']
   
    print(token)
    print("token printed")
    # header = request.headers.get("Authorization", None)
    # print(header)
    if not token:
        raise AuthError({"code": "authorization_header_missing",
                        "description":
                            "Authorization header is missing"}, 401)

    # splits = header.split()

    # if len(splits) != 2:
    #     raise AuthError({"code": "invalid_header",
    #                     "description":
    #                         "Authorization header must be"
    #                         " Bearer token"}, 401)
    # elif splits[0].lower() != "bearer":
    #     raise AuthError({"code": "invalid_header",
    #                     "description":
    #                         "Authorization header must start with"
    #                         " Bearer"}, 401)
    

    # token = splits[1]

    return token   

'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload
    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    print("inside check_permissions"+ permission)
    print(payload)
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_payload',
            'description': 'Permissions are Not included',
        }, 401)
    elif permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission Not found',
        }, 401)
    return True

'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    print("token:::"+ token)
    rsa_key = {}

    jsonurl = urlopen(f'https://audacity-fsnd-sarbani.uk.auth0.com/.well-known/jwks.json')
    print("jsonurl:::")

    jwks = json.loads(jsonurl.read())

    unverified_header = jwt.get_unverified_header(token)
    print(unverified_header)
    
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)
    print("unverified_header:::1") 
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    print("unverified_header:::2")
    if rsa_key:
        try:
            print("unverified_header:::3")
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            print("payload:::")
            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(session, permission=''):
    print("inside requires auth1")
    def requires_auth_decorator(f):
        print("inside requires_auth_decorator")
        @wraps(f)
        def wrapper(*args, **kwargs):
            print("insude requires auth2")
            token = get_token_auth_header(session)
            try:
                payload = verify_decode_jwt(token)
            except:
                abort(403)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator