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

    def button_workflow_action(self):
        pass

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(JunariWorkflowMixin, self)._fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)

        if view_type == 'form':
            arch = res['arch']

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
                        buttons_xml += ' type="object" name="button_workflow_action"'
                        buttons_xml += ' context="{\'workflow_transition\':\'%s/%s\'}"' % (
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

            res['arch'] = arch

        return res
