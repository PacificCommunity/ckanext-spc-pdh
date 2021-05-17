import hashlib
import base64
import re
import secrets
import logging

from typing import Any, NamedTuple, Optional

import six
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError
import ckan.model as model
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from ckan.exceptions import CkanConfigurationException

from ckanext.spc.model.drupal_user import DrupalUser

log = logging.getLogger(__name__)


class UserData(NamedTuple):
    name: str
    mail: str
    uid: str


def _db_url() -> Optional[str]:
    return tk.config.get("spc.drupal.db_url")


def _drupal_session_name():
    """Compute name of the cookie that stores Drupal's SessionID.

    For D9 it's PREFIX + HASH, where:
      PREFIX: if isHTTPS then SSESS else SESS
      HASH: first 32 characters of sha256 hash of the site's hostname
            (does not include port)

    """
    server_name = tk.request.environ["HTTP_HOST"].split(":")[0]
    name = (
        "SESS%s"
        % hashlib.sha256(six.ensure_binary(server_name)).hexdigest()[:32]
    )
    if tk.config.get("ckan.site_url").startswith("https"):
        name = "S" + name
    return name


def _make_password():
    return secrets.token_urlsafe(60)


def _sanitize_username(name):
    """Convert Drupal's username into CKAN's username.

    Drupal's usernames are allowed to contain spaces and other special
    characters that are not valid in CKAN's usernames.

    # FIXME: consider using `ckan.lib.munge:munge_name`

    """
    # convert spaces and separators
    name = re.sub("[ .:/]", "-", name).lower()
    # take out not-allowed characters
    name = re.sub("[^a-z0-9_-]", "", name)
    # remove doubles
    name = re.sub("--+", "-", name)
    # remove leading or trailing hyphens
    name = name.strip("-")[:99]
    return name


def _get_user_data_by_sid(sid: str) -> Optional[UserData]:
    """Fetch user data from Drupal's database.

    Only necessary fields are taken in order to reduce maintenance
    complexity in future, if DB structure changes. Method was
    written according to D9's table structure.

    """
    engine = sa.create_engine(_db_url())
    try:
        user = engine.execute(
            """
        SELECT d.name, d.mail, d.uid
        FROM sessions s
        JOIN users_field_data d
        ON s.uid = d.uid
        WHERE s.sid = %s
        """,
            [sid],
        )
    except OperationalError:
        log.exception("Cannot get a user from Drupal's database")
        return
    return user.first()


def _get_sid_from_cookies(cookies) -> Optional[str]:
    """Parse Drupal's session cookie and turn it into SessionID.

    This method was written around Drupal v9.1.4 release. It's
    logic is unlikely to change for D9, but it may change in the
    future major releases, so keep an eye on it and check it first
    if you are sure that session cookie is there, but CKAN can't
    obtain user from Drupal's database.

    Algorythm:
    - get cookie value
    - sha256 it
    - base64 it
    - replace pluses and slashes
    - strip out `=`-paddings

    """
    cookie_sid = cookies.get(_drupal_session_name())
    if not cookie_sid:
        return
    sha_hash = hashlib.sha256(six.ensure_binary(cookie_sid)).digest()
    base64_hash = base64.encodebytes(sha_hash)
    trans_rules = str.maketrans({"+": "-", "/": "_", "=": "",})
    sid = six.ensure_str(base64_hash.strip()).translate(trans_rules)
    return sid


def _get_user(user_id, email) -> dict:
    user = None

    if user_id:
        try:
            user = tk.get_action("user_show")(
                {
                    "keep_sensitive_data": True,
                    "keep_email": True,
                },
                {"id": user_id},
            )
        except tk.ObjectNotFound:
            user = None

    if not user:
            user_obj = (
                model.Session.query(model.User.id)
                .filter(model.User.email == email)
                .first()
            )
            if user_obj is not None:
                user = tk.get_action("user_show")(
                    {
                        "keep_sensitive_data": True,
                        "keep_email": True,
                    },
                    {"id": user_obj.id},
                )

    return user


def _save_drupal_user_id(ckan_user_id, drupal_user_id):
    user = DrupalUser.get_or_add(ckan_user_id, drupal_user_id)
    model.Session.commit()
    return user


def _sync_user_fields(user: dict, user_data: UserData) -> dict:
    """Make sure that user's name and email are in sync with Drupal's
    values.

    Raises:
    ValidationError if email is not unique
    """
    if user_data.mail != user["email"]:
        user["email"] = user_data.mail

        user = tk.get_action("user_update")(
            {"ignore_auth": True, "user": ""}, user
        )

    if user_data.name != user["name"]:
        User = model.Session.query(model.User).get(user["id"])
        User.name = _sanitize_username(user_data.name)
        model.Session.commit()
        # get user again after changes in user model
        user = _get_user(user["id"], user_data.mail)

    return user


def _create_user_from_user_data(user_data: UserData) -> dict:
    """Create a user with random password using Drupal's data.

    Raises:
    ValidationError if email is not unique
    """
    user = {
        "email": user_data.mail,
        "name": _sanitize_username(user_data.name),
        "password": _make_password(),
    }

    user = tk.get_action("user_create")(
        {"ignore_auth": True, "user": ""}, user
    )
    # save drupal user ID
    _save_drupal_user_id(user["id"], str(user_data.uid))
    return user


def _login_user(user_data: UserData):
    # getting CKAN user if exists

    ckan_uid = DrupalUser.get_or_add(
        ckan_user=None, drupal_user=str(user_data.uid)
    )

    try:
        user_id = ckan_uid.ckan_user
    except AttributeError:
        user_id = None

    try:
        user = _get_user(user_id, user_data.mail)
    except tk.ObjectNotFound:
        user = None

    # if we found user by email, we should "map" the ids
    if user and not user_id:
        _save_drupal_user_id(user["id"], str(user_data.uid))
        user_id = user["id"]
    try:
        if user:
            user = _sync_user_fields(user, user_data)
        else:
            user = _create_user_from_user_data(user_data)
    except tk.ValidationError as e:
        log.error('Cannot save user: %s', e)
        return
    tk.c.user = user["name"]


class SpcUserPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IAuthenticator, inherit=True)
    plugins.implements(plugins.IConfigurer)

    # IAuthenticator

    def identify(self):
        """ This does drupal authorization.
        The drupal session contains the drupal id of the logged in user.
        We need to convert this to represent the ckan user. """

        sid = _get_sid_from_cookies(tk.request.cookies)
        if not sid:
            return
        user_data = _get_user_data_by_sid(sid)
        if not user_data:
            return
        # check if session has username,
        # otherwise is unauthenticated user session
        if user_data.name:
            _login_user(user_data)

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, "spc_user/templates")
        if not _db_url():
            raise CkanConfigurationException(
                "Drupal9 extension has not been configured"
            )
