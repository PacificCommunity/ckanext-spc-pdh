# -*- coding: utf-8 -*-

import ckan.model as model
from ckan.common import _, g
from ckan.plugins import toolkit
from flask import Blueprint


def switch_admin_state(id):
    if not toolkit.check_access('sysadmin', {'user': g.user}):
        return toolkit.abort(403, _('Not authorized'))

    user = model.User.get(id)
    if not user:
        return toolkit.abort(404, _('User does not exist'))
    if g.user == user.name:
        return toolkit.abort(403, _('Not authorized'))
    user.sysadmin = not user.sysadmin
    user.save()

    return toolkit.redirect_to('user.read', id=id)


spc_user = Blueprint('spc_user', __name__)

spc_user.add_url_rule(u'/user/switch_admin_state/<id>',
                      view_func=switch_admin_state,
                      methods=(u'POST', ))
blueprints = [spc_user]
