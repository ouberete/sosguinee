"""Translate empty Django gettext entries with the DeepL API."""

import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import polib
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from decouple import config


PLACEHOLDER_RE = re.compile(
    r"%\([^)]+\)[#0\- +]?(?:\d+)?(?:\.\d+)?[a-zA-Z]"
    r"|%%|%[a-zA-Z]"
    r"|\{\{.*?\}\}|\{%.*?%\}|<[^>]+>",
    re.DOTALL,
)


def protect_placeholders(text):
    replacements = []

    def replace(match):
        token = f"ZZPLACEHOLDER{len(replacements):04d}ZZ"
        replacements.append((token, match.group(0)))
        return token

    return PLACEHOLDER_RE.sub(replace, text), replacements


def restore_placeholders(text, replacements):
    for token, value in replacements:
        if token not in text:
            raise CommandError(f"The translation service removed placeholder {token}.")
        text = text.replace(token, value)
    return text


class Command(BaseCommand):
    help = "Fill empty gettext translations in a .po file using DeepL."

    def add_arguments(self, parser):
        parser.add_argument("-l", "--language", default="en")
        parser.add_argument("--batch-size", type=int, default=30)

    def handle(self, *args, **options):
        language = options["language"]
        if language != "en":
            raise CommandError("This command currently supports only -l en.")

        api_key = os.environ.get("DEEPL_AUTH_KEY") or config("DEEPL_AUTH_KEY", default="")
        if not api_key:
            raise CommandError(
                "Set DEEPL_AUTH_KEY in your local environment before translating."
            )

        if options["batch_size"] < 1 or options["batch_size"] > 50:
            raise CommandError("--batch-size must be between 1 and 50.")

        po_path = settings.BASE_DIR / "locale" / language / "LC_MESSAGES" / "django.po"
        if not po_path.exists():
            raise CommandError(f"Translation catalog not found: {po_path}")

        catalog = polib.pofile(str(po_path))
        pending = [
            entry for entry in catalog
            if not entry.obsolete and entry.msgid and not entry.msgstr
        ]
        if not pending:
            self.stdout.write(self.style.SUCCESS("No empty translations found."))
            return

        endpoint = (
            "https://api-free.deepl.com/v2/translate"
            if api_key.endswith(":fx")
            else "https://api.deepl.com/v2/translate"
        )
        updates = {}
        batch_size = options["batch_size"]

        for offset in range(0, len(pending), batch_size):
            entries = pending[offset : offset + batch_size]
            source_texts = []
            protected = []
            for entry in entries:
                text, tokens = protect_placeholders(entry.msgid)
                source_texts.append(text)
                protected.append(tokens)
                if entry.msgid_plural:
                    plural, plural_tokens = protect_placeholders(entry.msgid_plural)
                    source_texts.append(plural)
                    protected.append(plural_tokens)

            payload = json.dumps({
                "text": source_texts,
                "source_lang": "FR",
                "target_lang": "EN-US",
                "preserve_formatting": True,
            }).encode("utf-8")
            request = Request(
                endpoint,
                data=payload,
                headers={
                    "Authorization": f"DeepL-Auth-Key {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urlopen(request, timeout=45) as response:
                    result = json.loads(response.read().decode("utf-8"))
            except (HTTPError, URLError, TimeoutError) as exc:
                raise CommandError(f"DeepL request failed: {exc}") from exc
            except (json.JSONDecodeError, KeyError) as exc:
                raise CommandError("DeepL returned an invalid response.") from exc

            translated = result.get("translations", [])
            if len(translated) != len(source_texts):
                raise CommandError("DeepL returned an unexpected number of translations.")

            cursor = 0
            for entry in entries:
                singular = restore_placeholders(translated[cursor]["text"], protected[cursor])
                cursor += 1
                if entry.msgid_plural:
                    plural = restore_placeholders(translated[cursor]["text"], protected[cursor])
                    cursor += 1
                    updates[entry] = {"0": singular, "1": plural}
                else:
                    updates[entry] = singular

            self.stdout.write(f"Translated {min(offset + len(entries), len(pending))}/{len(pending)} entries")

        for entry, translation in updates.items():
            if isinstance(translation, dict):
                entry.msgstr_plural = translation
            else:
                entry.msgstr = translation

        catalog.metadata["Language"] = "en"
        catalog.metadata["Plural-Forms"] = "nplurals=2; plural=(n != 1);"
        catalog.save(str(po_path))
        self.stdout.write(self.style.SUCCESS(f"Updated {len(updates)} entries in {po_path}."))
