from app.tasks import calculate
def test_addition(): assert calculate({"operation":"add","a":2,"b":3})["result"]==5
def test_division(): assert calculate({"operation":"divide","a":10,"b":2})["result"]==5
def test_sum(): assert calculate({"operation":"sum","numbers":[1,2,3]})["result"]==6
def test_division_by_zero():
    try: calculate({"operation":"divide","a":1,"b":0})
    except ValueError as exc: assert "zero" in str(exc)
    else: raise AssertionError("Expected ValueError")
def test_no_eval():
    try: calculate({"operation":"eval","expression":"__import__('os').system('id')"})
    except ValueError as exc: assert "Unsupported" in str(exc)
    else: raise AssertionError("Expected ValueError")
