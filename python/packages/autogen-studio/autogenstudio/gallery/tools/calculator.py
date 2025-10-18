import logging

from autogen_core.tools import FunctionTool

# Set up logging for better error tracking
logger = logging.getLogger(__name__)


def calculator(a: float, b: float, operator: str) -> str:
    """
    Improved calculator with better error handling and Korean error messages.

    Args:
        a: First number
        b: Second number
        operator: Operator (+, -, *, /)

    Returns:
        Result as string with Korean error messages if needed
    """
    try:
        # Validate inputs
        if not isinstance(a, (int, float)):
            return "오류: 첫 번째 숫자가 유효하지 않습니다"
        if not isinstance(b, (int, float)):
            return "오류: 두 번째 숫자가 유효하지 않습니다"
        if not isinstance(operator, str):
            return "오류: 연산자가 유효하지 않습니다"

        # Perform calculation with proper error handling
        if operator == "+":
            result = a + b
        elif operator == "-":
            result = a - b
        elif operator == "*":
            result = a * b
        elif operator == "/":
            if b == 0:
                return "오류: 0으로 나눌 수 없습니다"
            result = a / b
        else:
            return f"오류: 잘못된 연산자입니다. +, -, *, / 중 하나를 사용하세요. 입력값: '{operator}'"

        # Format result appropriately
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(round(result, 10))  # Limit decimal places for precision

    except TypeError as e:
        logger.error(f"Calculator TypeError: {e}")
        return f"오류: 타입 오류 - {str(e)}"
    except ValueError as e:
        logger.error(f"Calculator ValueError: {e}")
        return f"오류: 값 오류 - {str(e)}"
    except Exception as e:
        logger.error(f"Calculator unexpected error: {e}")
        return f"오류: 예상치 못한 오류가 발생했습니다 - {str(e)}"


# Create improved calculator tool with Korean description
calculator_tool = FunctionTool(
    name="calculator",
    description="기본 산술 연산을 수행하는 계산기 도구 (덧셈, 뺄셈, 곱셈, 나눗셈). 안정적인 오류 처리 기능이 포함되어 있습니다.",
    func=calculator,
    global_imports=[],
)
