import math


class Calculator:
    def calculate(self, num1, num2, operator):
        try:
            num1 = float(num1)
            num2 = float(num2)
        except ValueError:
            return "Error: Invalid number"

        if operator == "+":
            return num1 + num2
        elif operator == "-":
            return num1 - num2
        elif operator == "*":
            return num1 * num2
        elif operator == "/":
            if num2 == 0:
                return "Error: Cannot divide by zero"
            return num1 / num2
        elif operator == "//":
            if num2 == 0:
                return "Error: Cannot divide by zero"
            return math.floor(num1 / num2)
        else:
            return "Error: Invalid operator"