"""Independently reviewed workflow expectations, not values read from workflows."""
from typing import Any

import yaml

from .paths import ROOT

CHECKOUT = "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON = "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
APP_TOKEN = "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1"
CONFIGURE_PAGES = "actions/configure-pages@45bfe0192ca1faeb007ade9deae92b16b8254a0d"
UPLOAD_PAGES = "actions/upload-pages-artifact@fc324d3547104276b827a68afc52ff2a11cc49c9"
DEPLOY_PAGES = "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e"
UPLOAD_ARTIFACT = "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
DOWNLOAD_ARTIFACT = "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c"
SETUP_NODE = "actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38"
SETUP_VALIDATION = "./.github/actions/setup-validation"
APPROVED_ACTIONS=frozenset((CHECKOUT,SETUP_PYTHON,APP_TOKEN,CONFIGURE_PAGES,UPLOAD_PAGES,DEPLOY_PAGES,UPLOAD_ARTIFACT,DOWNLOAD_ARTIFACT,SETUP_VALIDATION,SETUP_NODE))


def load_setup_action() -> dict[str,Any]:
    value=yaml.load((ROOT/'.github/actions/setup-validation/action.yml').read_text(encoding='utf-8'),Loader=yaml.BaseLoader)
    assert isinstance(value,dict)
    return value
