"""
    File containing constants useds in the rest of
    the program
"""

import config


URL_TELEGRAM = "https://api.telegram.org/bot{}/".format(config.TOKEN)
URL_GITHUB = "https://api.github.com/repos/TecProg-20181/T--botcultural/issues"

TODO = 'TODO'
DOING = 'DOING'
DONE = 'DONE'
HELP = """
 /new NOME
 /newIssue NOME
 /todo ID...
 /doing ID...
 /done ID...
 /delete ID...
 /list
 /listP
 /listIssues
 /rename ID NOME
 /renameIssue ID NOME
 /dependson ID ID...
 /duplicate ID
 /priority PRIORITY{low, medium, high} ID...
 /duedate DATE{YYYY-MM-DD} ID...
 /help
"""

# ICONS
NEW_ICON = '\U0001F195'
DOING_ICON = '\U000023FA'
DONE_ICON = '\U00002611'
TASK_ICON = '\U0001F4CB'
STATUS_ICON = '\U0001F4DD'
HI_PRIORITY_ICON = '\U0001F534'
MED_PRIORITY_ICON = '\U0001F535'
LOW_PRIORITY_ICON = '\U000026AA'
PRIORITY = {
    'high':'\U0001F534',
    'medium':'\U0001F535',
    'low':'\U000026AA'
}
CONFUSED_EMOJI = '\U0001F615'
THINKING_EMOJI = '\U0001F914'
WRITING_EMOJI = '\U0000270D'
ZANY_EMOJI = '\U0001F62C'
MONOCLE_EMOJI = '\U0001F9D0'