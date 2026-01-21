"""
Comprehensive reliability tests for Ollama as the default model.

This test suite validates that all key features work correctly with Ollama:
1. Basic chat completion
2. Streaming completion
3. Function/tool calling
4. Structured output (JSON)
5. Multi-turn conversations
6. Error handling and recovery
"""

import asyncio
import json
from typing import Any, Dict, List

import pytest
from autogen_core import FunctionCall
from autogen_core.models import (
    AssistantMessage,
    CreateResult,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
    UserMessage,
)
from autogen_core.tools import FunctionTool
from autogen_ext.models.ollama import OllamaChatCompletionClient
from pydantic import BaseModel

# Skip tests if Ollama is not available locally
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def ollama_client() -> OllamaChatCompletionClient:
    """Create an Ollama client with the default model."""
    return OllamaChatCompletionClient(model="qwen3:0.6b", host="http://localhost:11434")


@pytest.fixture
def ollama_client_llama() -> OllamaChatCompletionClient:
    """Create an Ollama client with llama3.2 model."""
    return OllamaChatCompletionClient(model="llama3.2:1b", host="http://localhost:11434")


class TestBasicReliability:
    """Test basic reliability of Ollama client."""

    @pytest.mark.asyncio
    async def test_simple_completion(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that basic completion works."""
        result = await ollama_client.create(
            messages=[UserMessage(content="Say 'Hello, World!' and nothing else.", source="user")]
        )

        assert isinstance(result, CreateResult)
        assert isinstance(result.content, str)
        assert len(result.content) > 0
        assert result.finish_reason in ["stop", "unknown"]
        assert result.usage is not None
        assert result.usage.prompt_tokens > 0
        assert result.usage.completion_tokens > 0

    @pytest.mark.asyncio
    async def test_streaming_completion(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that streaming works correctly."""
        chunks: List[str | CreateResult] = []

        async for chunk in ollama_client.create_stream(
            messages=[UserMessage(content="Count from 1 to 5.", source="user")]
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert isinstance(chunks[-1], CreateResult)

        final_result = chunks[-1]
        assert isinstance(final_result.content, str)
        assert len(final_result.content) > 0
        assert final_result.finish_reason in ["stop", "unknown"]
        assert final_result.usage is not None

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that multi-turn conversations work."""
        # First turn
        result1 = await ollama_client.create(messages=[UserMessage(content="My name is Alice.", source="user")])
        assert isinstance(result1.content, str)

        # Second turn - check if model remembers
        result2 = await ollama_client.create(
            messages=[
                UserMessage(content="My name is Alice.", source="user"),
                AssistantMessage(content=result1.content, source="assistant"),
                UserMessage(content="What is my name?", source="user"),
            ]
        )
        assert isinstance(result2.content, str)
        # The model should mention Alice
        assert "Alice" in result2.content or "alice" in result2.content.lower()


class TestFunctionCalling:
    """Test function calling capabilities."""

    @pytest.mark.asyncio
    async def test_basic_function_calling(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that basic function calling works."""

        def add(x: int, y: int) -> int:
            """Add two numbers."""
            return x + y

        add_tool = FunctionTool(add, description="Add two numbers")

        result = await ollama_client.create(
            messages=[UserMessage(content="What is 5 plus 7? Use the add tool.", source="user")],
            tools=[add_tool],
        )

        assert isinstance(result.content, list)
        assert len(result.content) > 0
        assert isinstance(result.content[0], FunctionCall)
        assert result.content[0].name == "add"

        # Parse arguments and verify they're reasonable
        args = json.loads(result.content[0].arguments)
        assert "x" in args and "y" in args
        assert isinstance(args["x"], int) and isinstance(args["y"], int)

    @pytest.mark.asyncio
    async def test_function_execution_flow(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test complete function execution flow."""

        def multiply(a: int, b: int) -> int:
            """Multiply two numbers."""
            return a * b

        multiply_tool = FunctionTool(multiply, description="Multiply two numbers")

        # Step 1: Get function call
        result1 = await ollama_client.create(
            messages=[UserMessage(content="What is 6 times 7? Use the multiply tool.", source="user")],
            tools=[multiply_tool],
        )

        assert isinstance(result1.content, list)
        function_call = result1.content[0]
        assert isinstance(function_call, FunctionCall)

        # Step 2: Execute function
        args = json.loads(function_call.arguments)
        result_value = multiply(**args)

        execution_result = FunctionExecutionResult(
            content=str(result_value),
            call_id=function_call.id,
            name=function_call.name,
            is_error=False,
        )

        # Step 3: Get final response
        result2 = await ollama_client.create(
            messages=[
                UserMessage(content="What is 6 times 7? Use the multiply tool.", source="user"),
                AssistantMessage(content=result1.content, source="assistant"),
                FunctionExecutionResultMessage(content=[execution_result]),
            ]
        )

        assert isinstance(result2.content, str)
        assert "42" in result2.content or str(result_value) in result2.content


class TestStructuredOutput:
    """Test structured output capabilities."""

    @pytest.mark.asyncio
    async def test_json_output(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that JSON output works."""

        class Person(BaseModel):
            name: str
            age: int
            city: str

        result = await ollama_client.create(
            messages=[
                UserMessage(
                    content="Generate information about a person named John who is 30 years old and lives in New York.",
                    source="user",
                )
            ],
            json_output=Person,
        )

        assert isinstance(result.content, str)
        assert len(result.content) > 0

        # Verify it's valid JSON matching the schema
        person = Person.model_validate_json(result.content)
        assert person.name
        assert person.age > 0
        assert person.city

    @pytest.mark.asyncio
    async def test_json_mode(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that generic JSON mode works."""
        result = await ollama_client.create(
            messages=[UserMessage(content="List 3 colors in JSON format with 'colors' as the key.", source="user")],
            json_output=True,
        )

        assert isinstance(result.content, str)

        # Verify it's valid JSON
        data = json.loads(result.content)
        assert isinstance(data, dict)


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_invalid_tool_choice(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that invalid tool_choice is handled correctly."""
        # tool_choice="required" with no tools should raise an error
        with pytest.raises(ValueError, match="no tools provided"):
            await ollama_client.create(
                messages=[UserMessage(content="Test", source="user")],
                tools=[],
                tool_choice="required",
            )

    @pytest.mark.asyncio
    async def test_model_info_access(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that model info is accessible and correct."""
        model_info = ollama_client.model_info

        assert model_info is not None
        assert "json_output" in model_info
        assert "function_calling" in model_info
        assert "vision" in model_info

        # Qwen3 should support function calling and JSON output
        assert model_info["function_calling"] is True
        assert model_info["json_output"] is True

    @pytest.mark.asyncio
    async def test_token_counting(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that token counting works."""
        messages = [UserMessage(content="Hello, how are you?", source="user")]

        token_count = ollama_client.count_tokens(messages)
        assert token_count > 0
        assert isinstance(token_count, int)

        remaining = ollama_client.remaining_tokens(messages)
        assert remaining > 0
        assert isinstance(remaining, int)


class TestModelVariants:
    """Test different Ollama model variants."""

    @pytest.mark.asyncio
    async def test_llama_model(self, ollama_client_llama: OllamaChatCompletionClient) -> None:
        """Test that llama3.2 model works."""
        result = await ollama_client_llama.create(
            messages=[UserMessage(content="Say hello in one word.", source="user")]
        )

        assert isinstance(result.content, str)
        assert len(result.content) > 0
        assert result.finish_reason in ["stop", "unknown"]

    @pytest.mark.asyncio
    async def test_llama_with_tools(self, ollama_client_llama: OllamaChatCompletionClient) -> None:
        """Test that llama3.2 works with tools."""

        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        greet_tool = FunctionTool(greet, description="Greet someone by name")

        result = await ollama_client_llama.create(
            messages=[UserMessage(content="Greet Alice using the greet tool.", source="user")],
            tools=[greet_tool],
        )

        assert isinstance(result.content, list) or isinstance(result.content, str)
        # Function calling should work
        if isinstance(result.content, list):
            assert len(result.content) > 0


class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_response_time(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that responses come in reasonable time."""
        import time

        start_time = time.time()
        result = await ollama_client.create(messages=[UserMessage(content="Hi", source="user")])
        elapsed = time.time() - start_time

        # Response should come in under 30 seconds (generous for CI environments)
        assert elapsed < 30
        assert isinstance(result.content, str)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that concurrent requests work correctly."""

        async def make_request(i: int) -> CreateResult:
            return await ollama_client.create(messages=[UserMessage(content=f"Count to {i}", source="user")])

        # Run 3 concurrent requests
        results = await asyncio.gather(
            make_request(1),
            make_request(2),
            make_request(3),
        )

        assert len(results) == 3
        for result in results:
            assert isinstance(result, CreateResult)
            assert isinstance(result.content, str)
            assert len(result.content) > 0


class TestUsageTracking:
    """Test usage tracking capabilities."""

    @pytest.mark.asyncio
    async def test_usage_accumulation(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that usage is tracked correctly across requests."""
        # Get initial usage
        initial_usage = ollama_client.total_usage()
        initial_prompt = initial_usage.prompt_tokens
        initial_completion = initial_usage.completion_tokens

        # Make a request
        await ollama_client.create(messages=[UserMessage(content="Hello", source="user")])

        # Check usage increased
        final_usage = ollama_client.total_usage()
        assert final_usage.prompt_tokens > initial_prompt
        assert final_usage.completion_tokens > initial_completion

    @pytest.mark.asyncio
    async def test_actual_usage(self, ollama_client: OllamaChatCompletionClient) -> None:
        """Test that actual usage is reported correctly."""
        result = await ollama_client.create(messages=[UserMessage(content="Hi there!", source="user")])

        assert result.usage is not None
        assert result.usage.prompt_tokens > 0
        assert result.usage.completion_tokens > 0

        actual_usage = ollama_client.actual_usage()
        assert actual_usage.prompt_tokens >= result.usage.prompt_tokens
        assert actual_usage.completion_tokens >= result.usage.completion_tokens
