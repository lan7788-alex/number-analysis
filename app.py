def parse_shape_pick(text):
    text = (
        (text or "")
        .replace(" ", "")
        .replace("+", "")
        .replace("/", "")
        .replace("，", "")
        .replace(",", "")
    )

    size = None
    parity = None

    for s in SIZE_SHAPES:
        if s in text:
            size = s
            break

    for p in PARITY_SHAPES:
        if p in text:
            parity = p
            break

    if not size or not parity:
        return None, None

    return size, parity


def run_shape_pick(size_target, parity_target):
    full = [
        num for num in ALL_NUMBERS
        if (
            size_shape(num) == size_target
            and
            parity_shape(num) == parity_target
        )
    ]

    same23 = [
        num for num in full
        if repeat_type(num) != "三不同"
    ]

    different = [
        num for num in full
        if repeat_type(num) == "三不同"
    ]

    return (
        sorted(full),
        sorted(same23),
        sorted(different)
    )
