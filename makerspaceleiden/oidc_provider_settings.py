def userinfo(claims, user):
    claims['name'] = '{0} {1}'.format(user.first_name, user.last_name)
    claims['email'] = user.email
    return claims

