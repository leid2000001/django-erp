#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This file is part of the django ERP project.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

__author__ = 'Emanuele Bertoldi <emanuele.bertoldi@gmail.com>'
__copyright__ = 'Copyright (c) 2013 Emanuele Bertoldi'
__version__ = '0.0.3'

import copy
from django.test import TestCase

from ..models import *
from ..templatetags.menus import *

class RenderMenuTagTestCase(TestCase):
    urls = 'djangoerp.menus.tests.urls'

    def setUp(self):
        from django.template import Context
        from django.contrib.auth import get_user_model
        from djangoerp.core.models import Permission
        
        user_model = get_user_model()
        
        self.p, n = Permission.objects.get_or_create_by_natural_key("view_user", "core", "user")
        
        self.su = user_model.objects.create_superuser("su", "u@u.it", "password")
        self.u1 = user_model.objects.create_user("u1", "u@u.it", "password")
        self.u2 = user_model.objects.create_user("u2", "u@u.it", "password")
        self.u2.is_staff=True
        self.u2.save()
        self.u3 = user_model.objects.create_user("u3", "u@u.it", "password")
        self.u4 = user_model.objects.create_user("u4", "u@u.it", "password")
        
        self.u3.user_permissions.add(self.p)
        
        self.empty_m, n = Menu.objects.get_or_create(slug="empty-menu")
        
        self.m, n = Menu.objects.get_or_create(slug="valid-menu")
        self.l1, n = Link.objects.get_or_create(title="Link 1", slug="l1", url="/", only_authenticated=False, menu=self.m)
        self.l2, n = Link.objects.get_or_create(title="Link 2", slug="l2", url="", only_authenticated=False, menu=self.m)
        self.l3, n = Link.objects.get_or_create(title="Link 3", slug="l3", url="/", new_window=True, only_authenticated=False, menu=self.m)
        self.l4, n = Link.objects.get_or_create(title="Link 4", slug="l4", description="Another link.", url="private_zone_url", context='{"id": "link4_url_id_kwarg"}', only_authenticated=False, menu=self.m)
        self.l5, n = Link.objects.get_or_create(title="%(link5_title)s", slug="l5", url="%(link5_url)s", only_authenticated=False, menu=self.m)
        
        self.context = Context({
            "user": self.su,
            "menu_slug": self.m.slug,
            "menu_template": DEFAULT_MENU_TEMPLATE,
            "link4_url_id_kwarg": "1",
            "link5_title": "Link 5",
            "link5_url": "/link5"
        })
        
        self.auth_m, n = Menu.objects.get_or_create(slug="auth-menu")
        self.al1, n = Link.objects.get_or_create(title="Link 1", slug="al1", url="/", only_authenticated=False, menu=self.auth_m)
        self.al2, n = Link.objects.get_or_create(title="Link 2", slug="al2", url="/", menu=self.auth_m)
        self.al3, n = Link.objects.get_or_create(title="Link 3", slug="al3", url="/", only_staff=True, menu=self.auth_m)
        self.al4, n = Link.objects.get_or_create(title="Link 4", slug="al4", url="/", only_authenticated=False, menu=self.auth_m)
        self.al4.only_with_perms.add(self.p)
        
        self.auth_context = Context({
            "object": self.u1
        })
        
    def _clean_output(self, output):
        return "".join([r.strip() for r in output.strip().splitlines() if r and not r.isspace()])

    def test_render_invalid_menu(self):
        """Tests rendering an invalid menu.
        """
        output = render_menu({}, "invalid-menu")
        
        self.assertFalse(Menu.objects.filter(slug="invalid-menu").exists())
        self.assertEqual(output, "")
        
    def test_render_empty_menu(self):
        """Tests rendering an empty menu.
        """        
        output = render_menu({}, "empty-menu")
        
        self.assertEqual(output, "")
        
    def test_render_valid_menu(self):
        """Tests rendering a valid menu.
        """
        from django.template import Variable
        
        output = render_menu(
            self.context,
            Variable("menu_slug"),
            Variable("menu_template")
        )
        
        cleaned_output = self._clean_output(output)
        
        self.assertEqual(
            cleaned_output,
            '<ul id="valid-menu-menu" class="menu">'
            '<li id="l1-link">'
            '<a title="Link 1" href="/">'
            'Link 1'
            '</a>'
            '</li>'
            '<li id="l3-link">'
            '<a target="_blank" title="Link 3" href="/">'
            'Link 3'
            '</a>'
            '</li>'
            '<li id="l4-link">'
            '<a title="Another link." href="/private/1">'
            'Link 4'
            '</a>'
            '</li>'
            '<li id="l5-link">'
            '<a title="Link 5" href="/link5">'
            'Link 5'
            '</a>'
            '</li>'
            '</ul>'
        )
        
    def test_render_menu_with_invalid_user(self):
        """Tests managing invalid user on menu rendering.
        """        
        output = render_menu(
            self.auth_context,
            "auth-menu"
        )
        
        cleaned_output = self._clean_output(output)
        
        self.assertEqual(
            cleaned_output,
            '<ul id="auth-menu-menu" class="menu">'
            '<li id="al1-link">'
            '<a title="Link 1" href="/">'
            'Link 1'
            '</a>'
            '</li>'
            '</ul>'
        )
        
    def test_render_menu_with_anonymous_user_permission_management(self):
        """Tests handling anonymous user's permission management on menu rendering.
        """
        from django.contrib.auth.models import AnonymousUser
        
        context = copy.copy(self.auth_context)
        
        context['user'] = AnonymousUser()
        
        output = render_menu(
            context,
            "auth-menu"
        )
        
        cleaned_output = self._clean_output(output)
        
        self.assertEqual(
            cleaned_output,
            '<ul id="auth-menu-menu" class="menu">'
            '<li id="al1-link">'
            '<a title="Link 1" href="/">'
            'Link 1'
            '</a>'
            '</li>'
            '</ul>'
        )
        
    def test_render_menu_with_superuser_permission_management(self):
        """Tests handling superuser's permission management on menu rendering.
        """
        context = copy.copy(self.auth_context)
        
        context['user'] = self.su
        
        output = render_menu(
            context,
            "auth-menu"
        )
        
        cleaned_output = self._clean_output(output)
        
        self.assertEqual(
            cleaned_output,
            '<ul id="auth-menu-menu" class="menu">'
            '<li id="al1-link">'
            '<a title="Link 1" href="/">'
            'Link 1'
            '</a>'
            '</li>'
            '<li id="al2-link">'
            '<a title="Link 2" href="/">'
            'Link 2'
            '</a>'
            '</li>'
            '<li id="al3-link">'
            '<a title="Link 3" href="/">'
            'Link 3'
            '</a>'
            '</li>'
            '<li id="al4-link">'
            '<a title="Link 4" href="/">'
            'Link 4'
            '</a>'
            '</li>'
            '</ul>'
        )
        
    def test_render_menu_with_staff_user_permission_management(self):
        """Tests handling staff user's permission management on menu rendering.
        """
        context = copy.copy(self.auth_context)
        
        context['user'] = self.u2
        
        output = render_menu(
            context,
            "auth-menu"
        )
        
        cleaned_output = self._clean_output(output)
        
        self.assertEqual(
            cleaned_output,
            '<ul id="auth-menu-menu" class="menu">'
            '<li id="al1-link">'
            '<a title="Link 1" href="/">'
            'Link 1'
            '</a>'
            '</li>'
            '<li id="al2-link">'
            '<a title="Link 2" href="/">'
            'Link 2'
            '</a>'
            '</li>'
            '<li id="al3-link">'
            '<a title="Link 3" href="/">'
            'Link 3'
            '</a>'
            '</li>'
            '</ul>'
        )
        
    def test_render_menu_with_user_permission_management(self):
        """Tests handling user's permission management on menu rendering.
        """
        context = copy.copy(self.auth_context)
        
        context['user'] = self.u3
        
        output = render_menu(
            context,
            "auth-menu"
        )
        
        cleaned_output = self._clean_output(output)
        
        self.assertEqual(
            cleaned_output,
            '<ul id="auth-menu-menu" class="menu">'
            '<li id="al1-link">'
            '<a title="Link 1" href="/">'
            'Link 1'
            '</a>'
            '</li>'
            '<li id="al2-link">'
            '<a title="Link 2" href="/">'
            'Link 2'
            '</a>'
            '</li>'
            '<li id="al4-link">'
            '<a title="Link 4" href="/">'
            'Link 4'
            '</a>'
            '</li>'
            '</ul>'
        )
        
        