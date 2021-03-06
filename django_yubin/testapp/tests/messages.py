#!/usr/bin/env python
# encoding: utf-8
# ----------------------------------------------------------------------------

import functools
import os

from django.core.exceptions import ImproperlyConfigured
from django.core import mail
from django.test import TestCase
from django.template import Context, Template, TemplateDoesNotExist
from django.template.loader import get_template

from django_yubin.messages import (TemplatedEmailMessageView,
                                    TemplatedHTMLEmailMessageView,
                                    TemplatedAttachmentEmailMessageView)

from django.test.utils import override_settings


using_test_templates = override_settings(
    TEMPLATE_DIRS=(
        os.path.join(os.path.dirname(__file__), 'templates/mail'),
    ),
    TEMPLATE_LOADERS=(
        'django.template.loaders.filesystem.Loader',
    ),
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
)


class EmailMessageViewTestCase(TestCase):
    def run(self, *args, **kwargs):
        with using_test_templates:
            return super(EmailMessageViewTestCase, self).run(*args, **kwargs)

    def assertTemplateExists(self, name):
        try:
            get_template(name)
        except TemplateDoesNotExist:
            raise AssertionError('Template does not exist: %s' % name)

    def assertTemplateDoesNotExist(self, name):
        try:
            self.assertTemplateExists(name)
        except AssertionError:
            return
        raise AssertionError('Template exists: %s' % name)

    def assertOutboxLengthEquals(self, length):
        self.assertEqual(len(mail.outbox), length)


class TemplatedEmailMessageViewTestCase(EmailMessageViewTestCase):
    message_class = TemplatedEmailMessageView

    def setUp(self):
        self.message = self.message_class()

        self.template = 'Hello, world!'

        self.subject = 'subject'
        self.subject_template = Template('{{ subject }}')

        self.body = 'body'
        self.body_template = Template('{{ body }}')

        self.context_dict = {
            'subject': self.subject,
            'body': self.body,
        }

        self.context = Context(self.context_dict)

        self.render_subject = functools.partial(self.message.render_subject,
            context=self.context)
        self.render_body = functools.partial(self.message.render_body,
            context=self.context)

    def add_templates_to_message(self):
        """
        Adds templates to the fixture message, ensuring it can be rendered.
        """
        self.message.subject_template = self.subject_template
        self.message.body_template = self.body_template

    def test_subject_template_unconfigured(self):
        self.assertRaises(ImproperlyConfigured, self.render_subject)

    def test_subject_invalid_template_name(self):
        template = 'invalid.txt'
        self.assertTemplateDoesNotExist(template)

        self.message.subject_template_name = template
        self.assertRaises(TemplateDoesNotExist, self.render_subject)

    def test_subject_template_name(self):
        template = 'subject.txt'
        self.assertTemplateExists(template)

        self.message.subject_template_name = template
        self.assertEqual(self.render_subject(), self.subject)

    def test_subject_template(self):
        self.message.subject_template = self.subject_template
        self.assertEqual(self.render_subject(), self.subject)

    def test_body_template_unconfigured(self):
        self.assertRaises(ImproperlyConfigured, self.render_body)

    def test_body_invalid_template_name(self):
        template = 'invalid.txt'
        self.assertTemplateDoesNotExist(template)

        self.message.body_template_name = template
        self.assertRaises(TemplateDoesNotExist, self.render_body)

    def test_body_template_name(self):
        template = 'body.txt'
        self.assertTemplateExists(template)

        self.message.body_template_name = template
        self.assertEqual(self.render_body(), u"%s\n" % self.body)

    def test_body_template(self):
        self.message.body_template = self.body_template
        self.assertEqual(self.render_body(), self.body)

    def test_render_to_message(self):
        self.add_templates_to_message()
        message = self.message.render_to_message(self.context_dict)
        self.assertEqual(message.subject, self.subject)
        self.assertEqual(message.body, self.body)

    def test_send(self):
        self.add_templates_to_message()
        self.message.send(self.context_dict, to=('ted@disqus.com',))
        self.assertOutboxLengthEquals(1)

    def test_custom_headers(self):
        self.add_templates_to_message()
        address = 'ted@disqus.com'
        self.message.headers['Reply-To'] = address
        self.assertEqual(self.message.headers['Reply-To'], address)

        rendered = self.message.render_to_message()
        self.assertEqual(rendered.extra_headers['Reply-To'], address)

        rendered = self.message.render_to_message(headers={
            'References': 'foo',
        })
        self.assertEqual(rendered.extra_headers['Reply-To'], address)
        self.assertEqual(rendered.extra_headers['References'], 'foo')

    def test_priority_headers(self):
        """
        check if we can set the priority
        """

        self.add_templates_to_message()
        self.message.set_priority('low')
        self.assertEqual(self.message.headers['X-Mail-Queue-Priority'], 'low')

        rendered = self.message.render_to_message()
        self.assertEqual(rendered.extra_headers['X-Mail-Queue-Priority'], 'low')



class TemplatedHTMLEmailMessageViewTestCase(TemplatedEmailMessageViewTestCase):
    message_class = TemplatedHTMLEmailMessageView

    def setUp(self):
        super(TemplatedHTMLEmailMessageViewTestCase, self).setUp()

        self.html_body = 'html body'
        self.html_body_template = Template('{{ html }}')

        self.context_dict['html'] = self.html_body
        self.context['html'] = self.html_body

        self.render_html_body = functools.partial(
            self.message.render_html_body,
            context=self.context)

    def add_templates_to_message(self):
        """
        Adds templates to the fixture message, ensuring it can be rendered.
        """
        super(TemplatedHTMLEmailMessageViewTestCase, self)\
            .add_templates_to_message()
        self.message.html_body_template = self.html_body_template

    def test_html_body_template_unconfigured(self):
        self.assertRaises(ImproperlyConfigured, self.render_html_body)

    def test_html_body_invalid_template_name(self):
        template = 'invalid.txt'
        self.assertTemplateDoesNotExist(template)

        self.message.html_body_template_name = template
        self.assertRaises(TemplateDoesNotExist, self.render_html_body)

    def test_html_body_template_name(self):
        template = 'body.html'
        self.assertTemplateExists(template)

        self.message.html_body_template_name = template
        self.assertEqual(self.render_html_body(), u"%s\n" % self.html_body)

    def test_html_body_template(self):
        self.message.html_body_template = self.html_body_template
        self.assertEqual(self.render_html_body(), self.html_body)

    def test_render_to_message(self):
        self.add_templates_to_message()
        message = self.message.render_to_message(self.context_dict)
        self.assertEqual(message.subject, self.subject)
        self.assertEqual(message.body, self.body)
        self.assertEqual(message.alternatives, [(self.html_body, 'text/html')])

    def test_send(self):
        self.add_templates_to_message()
        self.message.send(self.context_dict, to=('ted@disqus.com',))
        self.assertOutboxLengthEquals(1)


class TemplatedAttachmentEmailMessageViewTestCase(TemplatedEmailMessageViewTestCase):
    message_class = TemplatedAttachmentEmailMessageView

    def setUp(self):
        super(TemplatedAttachmentEmailMessageViewTestCase, self).setUp()

        self.html_body = 'html body'
        self.html_body_template = Template('{{ html }}')

        self.context_dict['html'] = self.html_body
        self.context['html'] = self.html_body

        self.render_html_body = functools.partial(
            self.message.render_html_body,
            context=self.context)

    def add_templates_to_message(self):
        """
        Adds templates to the fixture message, ensuring it can be rendered.
        """
        super(TemplatedAttachmentEmailMessageViewTestCase, self)\
            .add_templates_to_message()
        self.message.html_body_template = self.html_body_template

    def test_render_to_message(self):
        self.add_templates_to_message()
        attachment = os.path.join(os.path.dirname(__file__), 'files/attachment.pdf'),
        message = self.message.render_to_message(extra_context=self.context_dict, attachment=attachment,
                                                 mimetype="application/pdf")
        self.assertEqual(message.subject, self.subject)
        self.assertEqual(message.body, self.body)
        self.assertEqual(message.alternatives, [(self.html_body, 'text/html')])
        self.assertEqual(len(message.attachments), 1)


class TemplatedAttachmentEmailMessageViewTestCase(TemplatedEmailMessageViewTestCase):
    message_class = TemplatedAttachmentEmailMessageView

    def setUp(self):
        super(TemplatedAttachmentEmailMessageViewTestCase, self).setUp()

        self.html_body = 'html body'
        self.html_body_template = Template('{{ html }}')

        self.context_dict['html'] = self.html_body
        self.context['html'] = self.html_body

        self.render_html_body = functools.partial(
            self.message.render_html_body,
            context=self.context)

    def add_templates_to_message(self):
        """
        Adds templates to the fixture message, ensuring it can be rendered.
        """
        super(TemplatedAttachmentEmailMessageViewTestCase, self)\
            .add_templates_to_message()
        self.message.html_body_template = self.html_body_template

    def test_render_to_message(self):
        self.add_templates_to_message()
        attachment = os.path.join(os.path.dirname(__file__), 'files/attachment.pdf'),
        message = self.message.render_to_message(extra_context=self.context_dict, attachment=attachment,
                                                 mimetype="application/pdf")
        self.assertEqual(message.subject, self.subject)
        self.assertEqual(message.body, self.body)
        self.assertEqual(message.alternatives, [(self.html_body, 'text/html')])
        self.assertEqual(len(message.attachments), 1)

    def test_send_message(self):
        """Test we can send an attachment using the send command"""
        self.add_templates_to_message()
        attachment = os.path.join(os.path.dirname(__file__), 'files/attachment.pdf')
        self.message.send(self.context_dict,
                          attachment=attachment,
                          mimetype="application/pdf",
                          to=('attachment@example.com',))
        self.assertOutboxLengthEquals(1)


class TestEmailOptions(EmailMessageViewTestCase):
    message_class = TemplatedEmailMessageView

    def setUp(self):
        self.message = self.message_class()

        self.template = 'Hello, world!'

        self.subject = 'subject'
        self.subject_template = Template('{{ subject }}')

        self.body = 'body'
        self.body_template = Template('{{ body }}')

        self.context_dict = {
            'subject': self.subject,
            'body': self.body,
        }

        self.context = Context(self.context_dict)

        self.render_subject = functools.partial(self.message.render_subject,
                                                context=self.context)
        self.render_body = functools.partial(self.message.render_body,
                                             context=self.context)

    def add_templates_to_message(self):
        """
        Adds templates to the fixture message, ensuring it can be rendered.
        """
        self.message.subject_template = self.subject_template
        self.message.body_template = self.body_template

    def test_send(self):
        self.add_templates_to_message()
        self.message.send(self.context_dict, to=('ted@disqus.com',))
        self.assertOutboxLengthEquals(1)

    def test_custom_headers(self):
        self.add_templates_to_message()
        address = 'ted@disqus.com'
        self.message.headers['Reply-To'] = address
        self.assertEqual(self.message.headers['Reply-To'], address)

        rendered = self.message.render_to_message()
        self.assertEqual(rendered.extra_headers['Reply-To'], address)

        rendered = self.message.render_to_message(headers={
            'References': 'foo',
        })
        self.assertEqual(rendered.extra_headers['Reply-To'], address)
        self.assertEqual(rendered.extra_headers['References'], 'foo')

    def test_priority_headers(self):
        """
        check if we can set the priority
        """

        self.add_templates_to_message()
        self.message.set_priority('low')
        self.assertEqual(self.message.headers['X-Mail-Queue-Priority'], 'low')

        rendered = self.message.render_to_message()
        self.assertEqual(rendered.extra_headers['X-Mail-Queue-Priority'], 'low')

