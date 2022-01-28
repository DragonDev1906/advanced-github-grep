import requests
from argparse import ArgumentParser
import json
import re
from searches.sqlinjection import SQLInjectionSearch
from utils import Search

NEWLINE_REPLACE_PATTERN = re.compile(r"\s*\n\s*", re.MULTILINE)

def parse_args():
    parser = ArgumentParser()
    # Output options
    group = parser.add_argument_group("Output options")
    group.add_argument("-c", "--count", action="store_true", help="Only count the number of occurances")
    group.add_argument("-n", "--remove-newlines", action="store_true", help="If this option is enabled all newline characters are removed from the output")
    group.add_argument("-j", "--join-tuple", action="store_true", help="If set the regex result tuple is joined together (each group entry is printed) instead of the tuple beeing shown.")

    return parser.parse_args()


def get_filtered_data_paginated(filter_pattern, ignore_case, regex_filter, whole_words, page=0):
    # https://grep.app/search?q=SELECT&regexp=true&case=true
    url = "https://grep.app/api/search"
    response = requests.get(url, params={
        "q": filter_pattern,
        "case": "true" if not ignore_case else "false",
        "regexp": "true" if regex_filter else "false",
        "words": "true" if whole_words else "false",
        "current": page
    })
    if response.status_code == 200:
        pass
    else:
        print("Unexpeted status code: ", response.status_code)
        print("Request: ", url)
        exit(1)
    data = json.loads(response.content)
    return data


def get_url_raw(repo, path):
    return "https://raw.githubusercontent.com/%s/master/%s" % (repo, path)

def get_url(repo, path):
    return "https://github.com/%s/blob/master/%s" % (repo, path)


def get_complete_file(repo, path):
    url = get_url_raw(repo, path)
    response = requests.get(url)
    if response.status_code == 200:
        pass
    elif response.status_code == 404:
        print("WARNING: File not found on github")
    else:
        print("Unexpeted status code: ", response.status_code)
        print("Request: ", url)
        exit(1)
    # Assuming the file is UTF-8 encoded
    return response.content.decode("UTF-8")


def search(file_content, pattern):
    results = pattern.findall(file_content)
    return results


def process_for_print(args, r):
    r = r.rstrip("\n")
    if args.remove_newlines:
        r = NEWLINE_REPLACE_PATTERN.sub(" ", r)
    return r


def print_findings(args, repo, path, result):
    print("%5i : %s" % (len(result), get_url(repo, path)))
    if not args.count:
        for r in result:
            if type(r) == str:
                r = (r, )
            r = [process_for_print(args, x) for x in r]
            
            print("\t", "".join(r) if args.join_tuple else r)


if __name__ == "__main__":
    args = parse_args()
    enabled_searches = [SQLInjectionSearch()]

    for search in enabled_searches:     # type: Search
        # TODO: Iterate over all pages instead of requesting only the first one
        data = get_filtered_data_paginated(search.filter_pattern, not search.case_sensitive, search.regex_filter, search.whole_words, 0)
        for entry in data["hits"]["hits"]:
            repo = entry["repo"]["raw"]
            path = entry["path"]["raw"]

            file_content = get_complete_file(repo, path)
            result = [x for x in search.run(file_content) if x is not None]
            print_findings(args, repo, path, result)
