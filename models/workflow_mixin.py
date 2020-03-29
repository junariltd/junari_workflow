from odoo import models, fields, api
from odoo.tools import config
from os import path
from yaml import load, SafeLoader
import re
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def get_workflow_file_abspath(filename):
    addons_path = config['addons_path'].split(',')
    for addons_folder in addons_path:
        try_file = path.join(addons_folder, filename)
        if path.isfile(try_file):
            return try_file
    raise Exception(
        'Could not find workflow file "%s" in addons paths.' % filename)


WORKFLOW_BUTTONS_REGEX = r'<workflow_buttons */>'
WORKFLOW_STATUSBAR_REGEX = r'<workflow_statusbar */>'

WORKFLOW_TRANSITION_BUTTONS_REGEX = r'<workflow_transition_buttons */>'
WORKFLOW_TRANSITION_FIELDS_REGEX = r'<workflow_transition_fields */>'


class JunariWorkflowMixin(models.AbstractModel):

    _name = 'junari.workflow'
    _description = 'Junari Workflow Mixin'

    @api.model
    def _setup_complete(self):
        res = super(JunariWorkflowMixin, self)._setup_complete()
        cls = type(self)
        workflow_file = getattr(self, '_workflow', False)
        if workflow_file:
            wkf_file_abspath = get_workflow_file_abspath(workflow_file)
            _logger.debug('Loading workflow for: %s from %s'
                          % (self._name, workflow_file))
            with open(wkf_file_abspath, 'r') as yamlfile:
                cls._workflow_definition = load(yamlfile, SafeLoader)

        return res

    def _workflow_get_states(self):
        return [
            (s['name'], s['label']) for s in self._workflow_definition['states']
        ]

    def _workflow_get_transition(self, state_name, trans_name):
        for state in self._workflow_definition['states']:
            if state.get('name') == state_name:
                for trans in state.get('transitions'):
                    if trans.get('name') == trans_name:
                        return (state, trans)
        return (False, False)

    def _workflow_get_transition_from_context(self):
        context = self.env.context
        state_name = context.get('workflow_state', False)
        trans_name = context.get('workflow_transition', False)
        if not state_name or not trans_name:
            raise Exception(
                'Workflow state or transition not found in context.')
        state, trans = self._workflow_get_transition(
            state_name, trans_name)
        if not state or not trans:
            raise Exception(
                'Workflow state transition "%s/%s" not found.' % (state_name, trans_name))
        return (state, trans)

    def button_workflow_transition(self):
        context = self.env.context
        state, trans = self._workflow_get_transition_from_context()
        transition_screen = trans.get('transition_screen', False)
        transition_confirmed = context.get(
            'workflow_transition_confirmed', False)
        if transition_screen and not transition_confirmed:
            workflow_transition_view_id = self.env.ref(
                self._workflow_transition_view)
            for rec in self:
                return {
                    'type': 'ir.actions.act_window',
                    'name': transition_screen.get('title', 'Workflow Transition'),
                    'res_model': self._name,
                    'res_id': rec.id,
                    'view_mode': 'form',
                    'view_id': workflow_transition_view_id.id,
                    'target': 'new',
                    'context': {}
                }
        new_state = trans.get('new_state', False)
        if new_state:
            self.write({'state': new_state})
        if transition_screen:
            return {'type': 'ir.actions.act_window_close'}

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(JunariWorkflowMixin, self)._fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        if view_type == 'form':
            arch = res['arch']
            context = self.env.context
            state_name = context.get('workflow_state', False)
            trans_name = context.get('workflow_transition', False)

            if re.search(WORKFLOW_STATUSBAR_REGEX, arch):
                display_states = [
                    s['name']
                    for s in self._workflow_definition['states']
                    if not s.get('statusbar_hide', False)
                ]
                arch = re.sub(
                    WORKFLOW_STATUSBAR_REGEX,
                    '<field name="state" widget="statusbar" statusbar_visible="%s" />'
                    % ','.join(display_states),
                    arch
                )

            if re.search(WORKFLOW_BUTTONS_REGEX, arch):
                buttons_xml = ''
                for state in self._workflow_definition['states']:
                    for trans in state['transitions']:
                        buttons_xml += '<button string="%s"' % trans['label']
                        buttons_xml += ' type="object" name="button_workflow_transition"'
                        buttons_xml += ' context="{\'workflow_state\':\'%s\',\'workflow_transition\':\'%s\'}"' % (
                            state['name'], trans['name'])
                        buttons_xml += ' states="%s"' % state['name']
                        if trans.get('class', False):
                            buttons_xml += ' class="%s"' % trans['class']
                        if trans.get('grouops', False):
                            buttons_xml += ' groups = "%s"' % trans['groups']
                        buttons_xml += ' />'
                arch = re.sub(
                    WORKFLOW_BUTTONS_REGEX,
                    buttons_xml,
                    arch
                )

            if re.search(WORKFLOW_TRANSITION_BUTTONS_REGEX, arch):
                state, trans = self._workflow_get_transition_from_context()
                buttons_xml = '<button string="%s" type="object"' % trans['label']
                buttons_xml += ' name="button_workflow_transition"'
                buttons_xml += (' context="{'
                                + '\'workflow_state\':\'%s\','
                                + '\'workflow_transition\':\'%s\','
                                + '\'workflow_transition_confirmed\':1}"'
                                ) % (state['name'], trans['name'])
                buttons_xml += ' class="oe_highlight" />'
                buttons_xml += '<button string="Cancel" special="cancel" />'
                arch = re.sub(
                    WORKFLOW_TRANSITION_BUTTONS_REGEX,
                    buttons_xml,
                    arch
                )

            if re.search(WORKFLOW_TRANSITION_FIELDS_REGEX, arch):
                state, trans = self._workflow_get_transition_from_context()
                transition_screen = trans.get('transition_screen', False)
                if not transition_screen:
                    raise Exception('Transition "%s/%s" does not define a transition_screen.' % (
                        state['name'], trans['name']))
                fields = transition_screen.get('fields', False)
                if not fields:
                    raise Exception('Transition "%s/%s" does not define transition_screen fields.' % (
                        state['name'], trans['name']))
                arch = re.sub(
                    WORKFLOW_TRANSITION_FIELDS_REGEX,
                    fields,
                    arch
                )

            res['arch'] = arch

        return res
