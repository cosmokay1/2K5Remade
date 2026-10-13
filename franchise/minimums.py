"""Published 2020 CBA Article 26 minimums; dollars, not cap charges.

The source table covers 2020-2030 and excludes practice-squad compensation.
Credited seasons and roster category must be supplied, not inferred from age,
overall rating, or years in the league. Amendments require a new rule version.
"""
SOURCE = "https://nflpaweb.blob.core.windows.net/website/PDFs/CBA/March-15-2020-NFL-NFLPA-Collective-Bargaining-Agreement-Final-Executed-Copy.pdf"
RULE_VERSION = "2020-cba-article26-minimums"

# Source tables are in thousands of dollars. Rows: 0, 1, 2, 3, 4-6, 7+ CS.
ACTIVE_INACTIVE = (
    (610, 660, 705, 750, 795, 840, 885, 930, 975, 1020, 1065),
    (675, 780, 825, 870, 915, 960, 1005, 1050, 1095, 1140, 1185),
    (750, 850, 895, 940, 985, 1030, 1075, 1120, 1165, 1210, 1255),
    (825, 920, 965, 1010, 1055, 1100, 1145, 1190, 1235, 1280, 1325),
    (910, 990, 1035, 1080, 1125, 1170, 1215, 1260, 1305, 1350, 1395),
    (1050, 1075, 1120, 1165, 1210, 1255, 1300, 1345, 1390, 1435, 1480),
)
NOT_ACTIVE_INACTIVE = (
    (400, 415, 430, 450, 470, 490, 515, 540, 565, 590, 615),
    (425, 440, 455, 475, 495, 515, 540, 565, 590, 615, 640),
    (450, 465, 480, 500, 520, 540, 565, 590, 615, 640, 665),
    (475, 490, 505, 525, 545, 565, 590, 615, 640, 665, 690),
    (500, 515, 530, 550, 570, 590, 615, 640, 665, 690, 715),
    (550, 565, 580, 600, 620, 640, 665, 690, 715, 740, 765),
)


def minimum_salary(year: int, credited_seasons: int, roster_category: str) -> int:
    if type(year) is not int or not 2020 <= year <= 2030:
        raise ValueError("Published minimum rules are available only for 2020-2030")
    if type(credited_seasons) is not int or credited_seasons < 0:
        raise ValueError("Verified nonnegative credited-season count required")
    if roster_category == "active_inactive":
        table = ACTIVE_INACTIVE
    elif roster_category == "not_active_inactive":
        table = NOT_ACTIVE_INACTIVE
    else:
        raise ValueError("Unsupported roster compensation category")
    row = credited_seasons if credited_seasons <= 3 else (4 if credited_seasons <= 6 else 5)
    return table[row][year - 2020] * 1000


def minimum_schedule(start_year: int, credited_seasons: tuple[int, ...],
                     roster_categories: tuple[str, ...]) -> tuple[int, ...]:
    """Use explicit annual projections; never assume a credited season is earned."""
    if type(start_year) is not int:
        raise ValueError("Integer start year required")
    if (type(credited_seasons) is not tuple or type(roster_categories) is not tuple
            or not credited_seasons or len(credited_seasons) != len(roster_categories)):
        raise ValueError("Matching nonempty annual season/category inputs required")
    return tuple(minimum_salary(start_year + i, count, category)
                 for i, (count, category) in enumerate(zip(credited_seasons, roster_categories)))
