from odoo import models, fields, api
from odoo.tools import config
from os import path
from yaml import load, SafeLoader
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
