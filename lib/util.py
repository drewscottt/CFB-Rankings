'''
'''

ESPN_URL_PREFIX = "https://www.espn.com"

def clip_to_range(x: float, min: float, max: float) -> float:
    if x > max:
        return max
    if x < min:
        return min
    return x