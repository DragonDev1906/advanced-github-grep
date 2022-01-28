from typing import List, Union, Tuple
from abc import ABC, abstractmethod
import re
import collections

class Search(ABC):
    filter_pattern: str
    case_sensitive = False
    regex_filter = False
    whole_words = False

    @abstractmethod
    def run(self, file_content) -> List[Union[str, Tuple[str], List[str]]]:
        """
        This is run for every file found by the filter.
        """
        pass

class RegexSearch(Search):
    pattern: re.Pattern

    def process_result(self, result: Union[str, Tuple[str], List[str]]) -> Union[str, Tuple[str], List[str],None]:
        """
        This is run for every result found by the regex pattern. It can be used to process the results before they are outputted
        """
        return result

    def run(self, file_content) -> List[Union[str, Tuple[str], List[str]]]:
        result = re.findall(self.pattern, file_content)
        return [self.process_result(r) for r in result]


def re_string_content(separation_char):
    return '(?:\\.|[^\\%s])*' % separation_char


def find_string_concatination_starting_at(start_index, file_content):
    # Output variables
    segments = []
    segment_start = start_index
    # Mode variables
    in_doublequote_string = False
    in_singlequote_string = False
    parenticies = collections.deque([])

    index = start_index
    while True:
        c = file_content[index]
        if in_doublequote_string:
            # Inside a "" string
            if c == '"':
                in_doublequote_string = False
            elif c == "\\":
                index += 1
        elif in_singlequote_string:
            # Inside a '' string
            if c == "'":
                in_singlequote_string = False
            elif c == "\\":
                index += 1
        else:
            if c == '"':
                in_doublequote_string = True
            elif c == "'":
                in_singlequote_string = True
            elif c in "([{":
                parenticies.append(c)
            elif c in ")]}":
                if len(parenthecies) == 0:
                    break
                else:
                    last = parenthecies.pop()
                    raise ValueError("Unexpected character: %s, expected: %s" % (c, last))
            elif c == "+" or (c == "." and file_content[index-1] == " "):
                if len(parenticies) == 0:
                    segments.append(file_content[segment_start:index])
                    segment_start = index + 1
            elif c in ",;":
                if len(parenthecies) == 0:
                    break

        index += 1

    segments.append(file_content[segment_start:index])
    return segments
