import gettext
import re
from hautoweb.settings import LANGUAGE_CODE, path

re_remove_domain = re.compile(r'^.{,20}///')

print path
print LANGUAGE_CODE
if LANGUAGE_CODE == "en-us":
    trans = gettext.NullTranslations()
else:
    trans = gettext.translation("homeauto", localedir="%s/locales" % path, languages=[LANGUAGE_CODE])

def _(text):
    text = trans.gettext(text)
    if type(text) == str:
        text = text.decode("utf-8")
    return re_remove_domain.sub('', text)
