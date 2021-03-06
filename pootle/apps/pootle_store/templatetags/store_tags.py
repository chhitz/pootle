#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django import template
from django.core.exceptions import ObjectDoesNotExist
#FIXME: _loader is probably not a stable API for the future, but seems like
# the best way to go for now:
from django.template.loaders.app_directories import _loader
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, ungettext

from translate.misc.multistring import multistring

from pootle_misc.templatetags.cleanhtml import fancy_escape, fancy_highlight
from pootle_misc.util import add_percentages, timezone
from pootle_store.fields import list_empty


register = template.Library()


def call_highlight(old, new):
    """Calls diff highlighting code only if the target is set.
    Otherwise, highlight as a normal unit.
    """
    if isinstance(old, multistring):
        old_value = old.strings
    else:
        old_value = old
    if list_empty(old_value):
        return fancy_highlight(new)
    else:
        return highlight_diffs(old, new)

def _google_highlight_diffs(old, new):
    """Highlights the differences between old and new."""

    textdiff = u""  # to store the final result
    removed = u""  # the removed text that we might still want to add
    diff = differencer.diff_main(old, new)
    differencer.diff_cleanupSemantic(diff)
    for op, text in diff:
        if op == 0:  # equality
            if removed:
                textdiff += '<span class="diff-delete">%s</span>' % fancy_escape(removed)
                removed = u""
            textdiff += fancy_escape(text)
        elif op == 1:  # insertion
            if removed:
                # this is part of a substitution, not a plain insertion. We
                # will format this differently.
                textdiff += '<span class="diff-replace">%s</span>' % fancy_escape(text)
                removed = u""
            else:
                textdiff += '<span class="diff-insert">%s</span>' % fancy_escape(text)
        elif op == -1:  # deletion
            removed = text
    if removed:
        textdiff += '<span class="diff-delete">%s</span>' % fancy_escape(removed)
    return mark_safe(textdiff)

def _difflib_highlight_diffs(old, new):
    """Highlights the differences between old and new. The differences
    are highlighted such that they show what would be required to
    transform old into new.
    """

    textdiff = ""
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, old, new).get_opcodes():
        if tag == 'equal':
            textdiff += fancy_escape(old[i1:i2])
        if tag == "insert":
            textdiff += '<span class="diff-insert">%s</span>' % fancy_escape(new[j1:j2])
        if tag == "delete":
            textdiff += '<span class="diff-delete">%s</span>' % fancy_escape(old[i1:i2])
        if tag == "replace":
            # We don't show text that was removed as part of a change:
            #textdiff += "<span>%s</span>" % fance_escape(a[i1:i2])}
            textdiff += '<span class="diff-replace">%s</span>' % fancy_escape(new[j1:j2])
    return mark_safe(textdiff)

try:
    from translate.misc.diff_match_patch import diff_match_patch
    differencer = diff_match_patch()
    highlight_diffs = _google_highlight_diffs
except ImportError, e:
    from difflib import SequenceMatcher
    highlight_diffs = _difflib_highlight_diffs


@register.filter('stat_summary')
def stat_summary(store):
    stats = add_percentages(store.getquickstats())
    # The translated word counts
    word_stats = _("Words Translated: %(translated)d/%(total)d - %(translatedpercent)d%%",
                   {"translated": stats['translatedsourcewords'],
                    "total": stats['totalsourcewords'],
                    "translatedpercent": stats['translatedpercentage']})
    word_stats = '<span class="word-statistics">%s</span>' % word_stats

    # The translated unit counts
    string_stats = _("Strings Translated: %(translated)d/%(total)d - %(translatedpercent)d%%",
                          {"translated": stats['translated'],
                           "total": stats['total'],
                          "translatedpercent": stats['strtranslatedpercentage']})
    string_stats = '<span class="string-statistics">%s</span>' % string_stats
    # The whole string of stats
    return mark_safe('%s &nbsp;&nbsp; %s' % (word_stats, string_stats))

@register.filter('pluralize_source')
def pluralize_source(unit):
    if unit.hasplural():
        count = len(unit.source.strings)
        if count == 1:
            return [(0, unit.source.strings[0], "%s+%s" % (_('Singular'), _('Plural')))]
        elif count == 2:
            return [(0, unit.source.strings[0], _('Singular')), (1, unit.source.strings[1], _('Plural'))]
        else:
            forms = []
            for i, source in enumerate(unit.source.strings):
                forms.append((i, source, _('Plural Form %d', i)))
            return forms
    else:
        return [(0, unit.source, None)]

@register.filter('pluralize_target')
def pluralize_target(unit, nplurals=None):
    if unit.hasplural():
        if nplurals is None:
            try:
                nplurals = unit.store.translation_project.language.nplurals
            except ObjectDoesNotExist:
                pass
        forms = []
        if nplurals is None:
            for i, target in enumerate(unit.target.strings):
                forms.append((i, target, _('Plural Form %d', i)))
        else:
            for i in range(nplurals):
                try:
                    target = unit.target.strings[i]
                except IndexError:
                    target = ''
                forms.append((i, target, _('Plural Form %d', i)))
        return forms
    else:
        return [(0, unit.target, None)]

@register.filter('pluralize_diff_sugg')
def pluralize_diff_sugg(sugg):
    unit = sugg.unit
    if unit.hasplural():
        forms = []
        for i, target in enumerate(sugg.target.strings):
            if i < len(unit.target.strings):
                forms.append((i, target, call_highlight(unit.target.strings[i], target), _('Plural Form %d', i)))
            else:
                forms.append((i, target, call_highlight('', target), _('Plural Form %d', i)))
        return forms
    else:
        return [(0, sugg.target, call_highlight(unit.target, sugg.target), None)]


def do_include_raw(parser, token):
    """
    Performs a template include without parsing the context, just dumps
    the template in.
    Source: http://djangosnippets.org/snippets/1684/
    """
    bits = token.split_contents()
    if len(bits) != 2:
        raise TemplateSyntaxError, "%r tag takes one argument: the name of the template to be included" % bits[0]

    template_name = bits[1]
    if template_name[0] in ('"', "'") and template_name[-1] == template_name[0]:
        template_name = template_name[1:-1]

    source, path = _loader.load_template_source(template_name)

    return template.TextNode(source)
register.tag("include_raw", do_include_raw)


@register.filter
def timedelta(date):
    """Returns a human-readable time delta, similar to Django's ``timesince``
    template filter but allowing proper localizability.

    Adapted from http://djangosnippets.org/snippets/2275/
    """
    delta = timezone.now() - date

    num_years = delta.days / 365
    if (num_years > 0):
        return ungettext(u"%d year ago",
                         u"%d years ago", num_years, num_years)

    num_weeks = delta.days / 7
    if (num_weeks > 0):
        return ungettext(u"%d week ago",
                         u"%d weeks ago", num_weeks, num_weeks)

    if (delta.days > 0):
        return ungettext(u"%d day ago",
                         u"%d days ago", delta.days, delta.days)

    num_hours = delta.seconds / 3600
    if (num_hours > 0):
        return ungettext(u"%d hour ago",
                         u"%d hours ago", num_hours, num_hours)

    num_minutes = delta.seconds / 60
    if (num_minutes > 0):
        return ungettext(u"%d minute ago",
                         u"%d minutes ago", num_minutes, num_minutes)

    return _(u"A few seconds ago")
