###############################################################################
#
# Copyright 2019, University of Stuttgart: Institute for Natural Language Processing (IMS)
#
# This file is part of Adviser.
# Adviser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3.
#
# Adviser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Adviser.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

from services.nlg.templates.data.expressions.variableexpression import VariableExpression
from services.nlg.templates.parsing.configuration import \
    StateDescription, Configuration, TransitionWithoutAction, DefaultTransition
from services.nlg.templates.parsing.exceptions import ParsingError
from services.nlg.templates.parsing.parsers.constraintparser.states.statelist import \
    VariableState, VariableEndState, OperatorState
from services.nlg.templates.parsing.stack import AutomatonStack


class _VariableDefaultTransition(DefaultTransition):
    def __init__(self):
        DefaultTransition.__init__(self, VariableState())

    def get_output_configuration(self, input_configuration: Configuration) -> Configuration:
        if not input_configuration.character.isalpha() and input_configuration.character != '_':
            raise ParsingError(f'Non-alpha character "{input_configuration.character}" detected.')
        return Configuration(input_configuration.state, input_configuration.character)

    def perform_stack_action(self, stack: AutomatonStack, configuration: Configuration):
        pass


class _VariableWhitespaceTransition(TransitionWithoutAction):
    def __init__(self):
        TransitionWithoutAction.__init__(self, Configuration(VariableState(), ' '),
                                         Configuration(VariableEndState(), ''))

    def perform_stack_action(self, stack: AutomatonStack, configuration: Configuration):
        current_content = stack.get_current_content()
        stack.add_data(VariableExpression(current_content))
        stack.remove_level()


class _TransitionFromArgumentToOperator(TransitionWithoutAction):
    def __init__(self):
        TransitionWithoutAction.__init__(self, Configuration(VariableState(), '='),
                                         Configuration(OperatorState(), ''))

    def perform_stack_action(self, stack: AutomatonStack, configuration: Configuration):
        current_content = stack.get_current_content()
        stack.add_data(VariableExpression(current_content))
        stack.remove_level()
        stack.add_level()


class VariableStateDescription(StateDescription):
    def __init__(self):
        StateDescription.__init__(self, VariableState(), _VariableDefaultTransition(), [
            _TransitionFromArgumentToOperator(),
            _VariableWhitespaceTransition()
        ])
