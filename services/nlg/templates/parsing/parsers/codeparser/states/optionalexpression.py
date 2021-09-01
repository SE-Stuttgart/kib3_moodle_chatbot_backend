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

from services.nlg.templates.parsing.configuration import StateDescription, \
    Configuration, TransitionWithAction, TransitionWithoutAction, DefaultTransition
from services.nlg.templates.parsing.exceptions import ParsingError
from services.nlg.templates.parsing.parsers.codeparser.states.statelist import \
    OptionalExpressionState, VariableState, StringState, ExpressionEndState
from services.nlg.templates.parsing.stack import AutomatonStack


class _ExpressionDefaultTransition(DefaultTransition):
    def __init__(self):
        DefaultTransition.__init__(self, OptionalExpressionState())

    def get_output_configuration(self, input_configuration: Configuration) -> Configuration:
        if not input_configuration.character.isalpha() and input_configuration.character != '_':
            raise ParsingError('Non-alpha character "{input_configuration.character}" detected.')
        return Configuration(VariableState(), input_configuration.character)

    def perform_stack_action(self, stack: AutomatonStack, configuration: Configuration):
        stack.add_level()


class OptionalExpressionStateDescription(StateDescription):
    def __init__(self):
        StateDescription.__init__(
            self, OptionalExpressionState(), _ExpressionDefaultTransition(), [
                TransitionWithoutAction(Configuration(OptionalExpressionState(), ' '),
                                        Configuration(OptionalExpressionState(), '')),
                TransitionWithAction(Configuration(OptionalExpressionState(), '"'),
                                     Configuration(StringState(), ''),
                                     lambda stack: stack.add_level()),
                TransitionWithAction(Configuration(OptionalExpressionState(), ')'),
                                     Configuration(ExpressionEndState(), ''),
                                     ExpressionEndState.add_function_to_stack)
            ])
