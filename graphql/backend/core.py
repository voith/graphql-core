import asyncio

from functools import partial
from six import string_types

from ..execution import execute, execute_async, ExecutionResult
from ..language.base import parse, print_ast
from ..language import ast
from ..validation import validate

from .base import GraphQLBackend, GraphQLDocument

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, Optional, Union, Tuple
    from ..language.ast import Document
    from ..type.schema import GraphQLSchema
    from rx import Observable


def _validate_document_ast(
        schema,  # type: GraphQLSchema
        document_ast,  # type: Document
        **kwargs  # type: Any
):
    # type: (...) -> Union[ExecutionResult, None]
    do_validation = kwargs.get("validate", True)
    if do_validation:
        validation_errors = validate(schema, document_ast)
        if validation_errors:
            return ExecutionResult(errors=validation_errors, invalid=True)
    return None


def execute_and_validate(
    schema,  # type: GraphQLSchema
    document_ast,  # type: Document
    *args,  # type: Any
    **kwargs  # type: Any
):
    # type: (...) -> Union[ExecutionResult, Observable]
    execution_result = _validate_document_ast(schema, document_ast, **kwargs)
    if execution_result:
        return execution_result

    return execute(schema, document_ast, *args, **kwargs)


@asyncio.coroutine
def execute_and_validate_async(
    schema,  # type: GraphQLSchema
    document_ast,  # type: Document
    *args,  # type: Any
    **kwargs  # type: Any
):
    # type: (...) -> Union[ExecutionResult, Observable]
    execution_result = _validate_document_ast(schema, document_ast, **kwargs)
    if execution_result:
        return execution_result
    result = yield from execute_async(schema, document_ast, *args, **kwargs)
    return result


class GraphQLCoreBackend(GraphQLBackend):
    """GraphQLCoreBackend will return a document using the default
    graphql executor"""

    def __init__(self, executor=None):
        # type: (Optional[Any]) -> None
        self.execute_params = {"executor": executor}

    @staticmethod
    def _get_doc_str_and_ast(document_string):
        # type: (Union[ast.Document, str]) -> Tuple[str, ast.Document]
        if isinstance(document_string, ast.Document):
            document_ast = document_string
            document_string = print_ast(document_ast)
        else:
            assert isinstance(
                document_string, string_types
            ), "The query must be a string"
            document_ast = parse(document_string)
        return document_string, document_ast

    def document_from_string(self, schema, document_string):
        # type: (GraphQLSchema, Union[ast.Document, str]) -> GraphQLDocument
        document_string, document_ast = self._get_doc_str_and_ast(document_string)
        return GraphQLDocument(
            schema=schema,
            document_string=document_string,
            document_ast=document_ast,
            execute=partial(
                execute_and_validate, schema, document_ast, **self.execute_params
            ),
        )

    def document_from_string_async(self, schema, document_string):
        # type: (GraphQLSchema, Union[ast.Document, str]) -> GraphQLDocument
        document_string, document_ast = self._get_doc_str_and_ast(document_string)
        return GraphQLDocument(
            schema=schema,
            document_string=document_string,
            document_ast=document_ast,
            execute=partial(
                execute_and_validate_async, schema, document_ast, **self.execute_params
            ),
        )
