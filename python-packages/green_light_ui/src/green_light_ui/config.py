"""

Config file for Streamlit App

"""

from member import Member


TITLE = "MLOPS Bootcamp - May 24"

TEAM_MEMBERS = [
    Member("Paula"),
    Member("Evan"),
    Member(
        name="Josef",
        linkedin_url="https://www.linkedin.com/in/dr-josef-hartmann-3663935/",
        github_url="https://github.com/DocJosef",
    ),
]

PROMOTION = "MLOPS Bootcamp - May 2024"
