def normalize(value):
    output = []
    pending_space = False
    for character in value:
        if character.isspace():
            if output:
                pending_space = True
        else:
            if pending_space:
                output.append(" ")
            output.append(character)
            pending_space = False
    return "".join(output)
