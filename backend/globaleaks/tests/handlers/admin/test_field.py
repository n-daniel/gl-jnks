# -*- coding: utf-8 -*-
import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers import admin
from globaleaks.handlers.node import anon_serialize_field
from globaleaks.handlers.admin.context import create_context
from globaleaks.handlers.admin.field import create_field
from globaleaks.rest import errors
from globaleaks.tests import helpers


@transact
def get_step_id(store, context_id):
    steps = store.find(models.Step, models.Step.context_id == context_id)
    return steps[0].id


class TestFieldCreate(helpers.TestHandler):
        _handler = admin.field.FieldCollection

        @inlineCallbacks
        def test_post(self):
            """
            Attempt to create a new field via a post request.
            """
            values = self.get_dummy_field()
            values['instance'] = 'instance'
            context = yield create_context(self.dummyContext, 'en')
            values['step_id'] = yield get_step_id(context['id'])
            handler = self.request(values, role='admin')
            yield handler.post()
            self.assertEqual(len(self.responses), 1)

            resp, = self.responses
            self.assertIn('id', resp)
            self.assertNotEqual(resp.get('options'), None)

        @inlineCallbacks
        def test_post_create_from_template(self):
            """
            Attempt to create a new field from template via post request
            """
            values = self.get_dummy_field()
            values['instance'] = 'template'
            field_template = yield create_field(values, 'en')

            context = yield create_context(copy.deepcopy(self.dummyContext), 'en')
            step_id = yield get_step_id(context['id'])

            values = self.get_dummy_field()
            values['instance'] = 'reference'
            values['template_id'] = field_template['id']
            values['step_id'] = yield get_step_id(context['id'])

            handler = self.request(values, role='admin')
            yield handler.post()
            self.assertEqual(len(self.responses), 1)

            resp, = self.responses
            self.assertIn('id', resp)
            self.assertNotEqual(resp.get('options'), None)


class TestFieldInstance(helpers.TestHandler):
        _handler = admin.field.FieldInstance

        @transact_ro
        def _get_children(self, store, field_id):
            field = models.Field.get(store, field_id)
            return [child.id for child in field.children]

        @inlineCallbacks
        def test_get(self):
            """
            Create a new field, then get it back using the received id.
            """
            values = self.get_dummy_field()
            values['instance'] = 'instance'
            context = yield create_context(copy.deepcopy(self.dummyContext), 'en')
            values['step_id'] = yield get_step_id(context['id'])
            field = yield create_field(values, 'en')

            handler = self.request(role='admin')
            yield handler.get(field['id'])
            self.assertEqual(len(self.responses), 1)
            self.assertEqual(field['id'], self.responses[0]['id'])

        @inlineCallbacks
        def test_put(self):
            """
            Attempt to update a field, changing its type via a put request.
            """
            values = self.get_dummy_field()
            values['instance'] = 'instance'
            context = yield create_context(copy.deepcopy(self.dummyContext), 'en')
            values['step_id'] = yield get_step_id(context['id'])
            field = yield create_field(values, 'en')

            updated_sample_field = self.get_dummy_field()
            updated_sample_field['instance'] = 'instance'
            context = yield create_context(copy.deepcopy(self.dummyContext), 'en')
            updated_sample_field['step_id'] = yield get_step_id(context['id'])
            updated_sample_field.update(type='inputbox')
            handler = self.request(updated_sample_field, role='admin')
            yield handler.put(field['id'])
            self.assertEqual(len(self.responses), 1)
            self.assertEqual(field['id'], self.responses[0]['id'])
            self.assertEqual(self.responses[0]['type'], 'inputbox')

            wrong_sample_field = self.get_dummy_field()
            values['instance'] = 'instance'
            values['step_id'] = yield get_step_id(context['id'])
            wrong_sample_field.update(type='nonexistingfieldtype')
            handler = self.request(wrong_sample_field, role='admin')
            self.assertFailure(handler.put(field['id']), errors.InvalidInputFormat)

        @inlineCallbacks
        def test_delete(self):
            """
            Create a new field, then attempt to delete it.
            """
            values = self.get_dummy_field()
            values['instance'] = 'instance'
            context = yield create_context(copy.deepcopy(self.dummyContext), 'en')
            values['step_id'] = yield get_step_id(context['id'])
            field = yield create_field(values, 'en')

            handler = self.request(role='admin')
            yield handler.delete(field['id'])
            self.assertEqual(handler.get_status(), 200)
            # second deletion operation should fail
            self.assertFailure(handler.delete(field['id']), errors.FieldIdNotFound)


class TestFieldTemplateInstance(helpers.TestHandlerWithPopulatedDB):
        _handler = admin.field.FieldTemplateInstance
        fixtures = ['fields.json']

        @transact_ro
        def _get_field(self, store, field_id):
            field = models.Field.get(store, field_id)
            return anon_serialize_field(store, field, 'en')

        @transact_ro
        def _get_children(self, store, field_id):
            field = models.Field.get(store, field_id)
            return [child.id for child in field.children]

        @inlineCallbacks
        def test_get(self):
            """
            Create a new field, the get it back using the receieved id.
            """
            values = self.get_dummy_field()
            values['instance'] = 'template'
            field = yield create_field(values, 'en')

            handler = self.request(role='admin')
            yield handler.get(field['id'])
            self.assertEqual(len(self.responses), 1)
            self.assertEqual(field['id'], self.responses[0]['id'])

        @inlineCallbacks
        def test_put_1(self):
            """
            Attempt to update a field, changing its type via a put request.
            """
            values = self.get_dummy_field()
            values['instance'] = 'template'
            field = yield create_field(values, 'en')

            updated_sample_field = self.get_dummy_field()
            updated_sample_field['instance'] = 'template'
            updated_sample_field['type'] ='inputbox'
            handler = self.request(updated_sample_field, role='admin')
            yield handler.put(field['id'])
            self.assertEqual(len(self.responses), 1)
            self.assertEqual(field['id'], self.responses[0]['id'])
            self.assertEqual(self.responses[0]['type'], 'inputbox')

            wrong_sample_field = self.get_dummy_field()
            wrong_sample_field.update(type='nonexistingfieldtype')
            handler = self.request(wrong_sample_field, role='admin')
            self.assertFailure(handler.put(field['id']), errors.InvalidInputFormat)

        @inlineCallbacks
        def test_put_2(self):
            """
            Update the field tree with nasty stuff, like cyclic graphs, inexisting ids.
            """
            generalities_fieldgroup_id = u'37242164-1b1f-1110-1e1c-b1f12e815105'
            sex_field_id = u'98891164-1a0b-5b80-8b8b-93b73b815156'
            surname_field_id = u'25521164-1d0f-5f80-8e8c-93f73e815156'
            name_field_id = u'25521164-0d0f-4f80-9e9c-93f72e815105'
            invalid_id = u'00000000-1d0f-5f80-8e8c-93f700000000'

            handler = self.request(role='admin')
            yield handler.get(generalities_fieldgroup_id)

            # simple edits shall work
            sex_field = yield self._get_field(sex_field_id)
            surname_field = yield self._get_field(surname_field_id)

            self.responses[0]['children'] = [sex_field,
                                             surname_field]

            handler = self.request(self.responses[0], role='admin')
            yield handler.put(generalities_fieldgroup_id)
            yield self.assert_model_exists(models.Field, generalities_fieldgroup_id)

            # parent MUST not refer to itself in child
            generalities_fieldgroup = yield self._get_field(generalities_fieldgroup_id)
            self.responses[0]['children'] = [generalities_fieldgroup]
            handler = self.request(self.responses[0], role='admin')
            self.assertFailure(handler.put(generalities_fieldgroup_id), errors.InvalidInputFormat)

            # a field not of type 'fieldgroup' MUST never have children.
            yield handler.get(name_field_id)
            sex_field = yield self._get_field(sex_field_id)
            self.responses[2]['children'] = [sex_field]
            handler = self.request(self.responses[2], role='admin')
            self.assertFailure(handler.put(name_field_id), errors.InvalidInputFormat)

            children = yield self._get_children(sex_field_id)
            self.assertNotIn(name_field_id, children)

        @inlineCallbacks
        def test_delete(self):
            """
            Create a new field template, then attempt to delete it.
            """
            values = self.get_dummy_field()
            values['instance'] = 'template'
            field = yield create_field(values, 'en')

            handler = self.request(role='admin')
            yield handler.delete(field['id'])
            self.assertEqual(handler.get_status(), 200)
            # second deletion operation should fail
            self.assertFailure(handler.delete(field['id']), errors.FieldIdNotFound)


class TestFieldTemplatesCollection(helpers.TestHandlerWithPopulatedDB):
        _handler = admin.field.FieldTemplatesCollection
        fixtures = ['fields.json']

        @inlineCallbacks
        def test_get(self):
            """
            Retrieve a list of all fields, and verify that they do exist in the
            database.
            """
            handler = self.request(role='admin')
            yield handler.get()
            fields, = self.responses

            ids = [field.get('id') for field in fields]
            types = [field.get('type') for field in fields]
            self.assertGreater(len(fields), 0)
            self.assertNotIn(None, ids)
            self.assertIn('37242164-1b1f-1110-1e1c-b1f12e815105', ids)
            self.assertGreater(types.count('fieldgroup'), 0)

            # check tha childrens are not present in the list
            # as the list should contain only parents fields
            for field in fields:
                for child in field['children']:
                    self.assertNotIn(child, ids)

        @inlineCallbacks
        def test_post(self):
            """
            Attempt to create a new field via a post request.
            """
            values = self.get_dummy_field()
            values['instance'] = 'template'
            handler = self.request(values, role='admin')
            yield handler.post()
            self.assertEqual(len(self.responses), 1)

            resp, = self.responses
            self.assertIn('id', resp)
            self.assertNotEqual(resp.get('options'), None)
