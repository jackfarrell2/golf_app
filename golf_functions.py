
def par_shift(score):
    if score == 0:
        return ("E")
    elif score > 0:
        return ("+{}".format(score))
    else:
        return str(score)

