from inputs import get_gamepad
while True:
    for e in get_gamepad():
        print(e.code, e.state)
