import json
import ast
import operator
import math
from difflib import get_close_matches

# --------------------------- Math Solver ---------------------------

allowed_ops = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg
}

# Allowed math functions
allowed_funcs = {name: getattr(math, name) for name in dir(math) if not name.startswith("__")}

# Math constants
constants = {"pi": math.pi, "e": math.e}

# Variables dictionary
variables = {}

def safe_eval_expr(node):
    # Handle numbers / constants
    if isinstance(node, ast.Constant):  # Replaces ast.Num
        return node.value
    if isinstance(node, ast.Name):
        if node.id in variables:
            return variables[node.id]
        elif node.id in allowed_funcs:
            return allowed_funcs[node.id]
        elif node.id in constants:
            return constants[node.id]
        else:
            raise ValueError(f"Unknown variable or function: {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in allowed_ops:
        return allowed_ops[type(node.op)](safe_eval_expr(node.left), safe_eval_expr(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_ops:
        return allowed_ops[type(node.op)](safe_eval_expr(node.operand))
    if isinstance(node, ast.Call):
        func_name = node.func.id
        if func_name in allowed_funcs:
            args = [safe_eval_expr(arg) for arg in node.args]
            return allowed_funcs[func_name](*args)
        else:
            raise ValueError(f"Function {func_name} not allowed")
    raise ValueError("Unsupported expression")

def solve_math_expression(expr: str):
    """Solve expressions or assignments with variables/functions/constants."""
    expr = expr.replace("^", "**")
    try:
        parsed = ast.parse(expr, mode='exec')
        result = None
        for node in parsed.body:
            if isinstance(node, ast.Assign):
                if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
                    return "Invalid assignment"
                var_name = node.targets[0].id
                variables[var_name] = safe_eval_expr(node.value)
                result = variables[var_name]
            elif isinstance(node, ast.Expr):
                result = safe_eval_expr(node.value)
            else:
                return "Unsupported statement"
        return result
    except Exception:
        return None

# --------------------------- KB Functions ---------------------------

def load_knowledge_base(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"questions": []}

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def find_best_match(user_question: str, questions: list) -> str | None:
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_answer_for_question(question: str, knowledge_base: dict) -> str:
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]

# --------------------------- Chat Bot ---------------------------

def chat_bot():
    knowledge_base = load_knowledge_base('knowledge_base.json')
    print("GooglBot: Hello! Ask me math questions or anything else. Type 'quit' to exit.")
    
    while True:
        user_input = input('You: ').strip()
        if user_input.lower() == 'quit':
            break

        # 1. Try solving math first
        math_result = solve_math_expression(user_input)
        if math_result is not None:
            print("GooglBot:", math_result)
            continue

        # 2. Try the knowledge base
        best_match = find_best_match(
            user_input,
            [q["question"] for q in knowledge_base["questions"]]
        )
        if best_match:
            answer = get_answer_for_question(best_match, knowledge_base)
            print("GooglBot:", answer)
            continue

        # 3. Ask to learn new answer
        print("GooglBot: I don't know the answer. Can you teach me?")
        new_answer = input('Type the answer or "skip" to skip: ').strip()
        if new_answer.lower() == 'skip':
            print("GooglBot: Okay, maybe next time.")
            continue

        knowledge_base['questions'].append({
            "question": user_input,
            "answer": new_answer
        })
        save_knowledge_base('knowledge_base.json', knowledge_base)
        print('GooglBot: Thank you! I learned a new response!')

if __name__ == '__main__':
    chat_bot()
