# Junari Workflow engine for Odoo

Model mixin for easily defining customisable worklow for Odoo entities

A `workflow.yml` for an entity defines:

* List of possible entity states
* Workflow buttons available in each state, and their target state
* Optional transition screens to display fields that must be entered
* TODO: Conditions for displaying those workflow buttons

## View Tags

This module supports the following tags in views

### Model View

In the model view, this module generates workflow buttons and statusbar when the following tags are used:

```xml
<field name="arch" type="xml">
    <form string="Case" >
        <header>
            <workflow_buttons />  <!-- Replaced with workflow buttons with appropriate rules based the current state -->
            <workflow_statusbar />  <!-- Replaced with field name="state" widget="statusbar" states="..." -->
        </header>
    <sheet>
```

### Workflow Transition View

You must create one workflow transition view for your model, which this module will populate with transition
fields as appropriate.

```xml
    <!-- Case Workflow Screen -->
    <record model="ir.ui.view" id="view_workflow_transition">
        <field name="name">jcrm.case.workflow_transition</field>
        <field name="model">jcrm.case</field>
        <field name="arch" type="xml">
            <form string="Workflow">
                <header>
                    <workflow_transition_buttons />
                    <workflow_statusbar />
                </header>
                <sheet>
                    <group>
                        <workflow_transition_fields />
                    </group>
                </sheet>
                <footer></footer>
            </form>
        </field>
    </record>
```

## Model Fields

To activate this module for a model, add the following data to your model:

```py
class Case(models.Model):
    _name = 'jcrm.case'
    _description = _("Case")
    _inherit = [..., 'junari.workflow']

    _workflow = 'jcrm_case/workflow/case_workflow.yml'
    _workflow_transition_view = 'jcrm_case.view_workflow_transition'

```

## Workflow Example

Simple example case workflow YAML

```yaml

states:

 - name: open
   label: Open
   transitions:

    - name: complete
      label: Complete
      class: oe_highlight
      groups: jcrm_case.group_jcrm_case_edit
      new_state: complete
      transition_screen:
        title: Complete Case
        fields: |
          <field name="solution" required="1" />
          <field name="user_id" required="1" />

    - name: onhold
      label: Put On Hold
      groups: jcrm_case.group_jcrm_case_edit
      new_state: onhold
      transition_screen:
        title: Put Case On Hold
        fields: |
          <field name="summary" required="1" />
          <field name="user_id" required="0" />

 - name: onhold
   label: On Hold
   statusbar_hide: True
   transitions:

    - name: reopen
      label: Re-Open
      class: oe_highlight
      groups: jcrm_case.group_jcrm_case_edit
      new_state: open  
      transition_screen:
        title: Re-Open Case
        fields: |
          <field name="summary" required="1" />
          <field name="user_id" required="1" />

 - name: complete
   label: Complete
   transitions:

    - name: close
      label: Close
      class: oe_highlight
      groups: jcrm_case.group_jcrm_case_edit
      new_state: closed
      transition_screen:
        title: Close Case
        fields: |
          <field name="solution" required="1" />

    - name: reopen
      label: Re-Open
      groups: jcrm_case.group_jcrm_case_edit
      new_state: open  
      transition_screen:
        title: Re-Open Case
        fields: |
          <field name="summary" required="1" />
          <field name="user_id" required="1" />

 - name: closed
   label: Closed
   transitions:

    - name: reopen
      label: Re-Open
      groups: jcrm_case.group_jcrm_case_edit
      new_state: open  
      # Transition Screens are optional :-)

```

# License

MIT