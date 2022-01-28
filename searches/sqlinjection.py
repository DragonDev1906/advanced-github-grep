from utils import *

SQL_START_PATTERNS = [
    "SELECT", 
    "DELETE", 
    "ALTER", 
    "ANALYSE", 
    "AUDIT", 
    "COMMENT", 
    "CREATE", 
    "DROP", 
    "FLASHBACK", 
    "GRANT", 
    "NOAUDIT", 
    "PURGE", 
    "RENAME", 
    "REVOKE", 
    "TRUNCATE"
]
SQL_START_LOOKAHEAD = '(?=%s)' % ('|'.join(SQL_START_PATTERNS))
STRING_CONTENT = re_string_content('"')
SQL_START = '"%s%s"' % (SQL_START_LOOKAHEAD, STRING_CONTENT)
CONCAT = r'\s*[+.]\s*'
VARIABLE_OR_FUNCTION = r'[\w_$.]'


class SQLInjectionSearch(RegexSearch):
    filter_pattern = '"(SELECT|DELETE|CREATE|DROP)'
    regex_filter = True
    case_sensitive = False
    pattern = "(" + SQL_START + CONCAT +")"
    
    def process_result(self, result):
        return result
