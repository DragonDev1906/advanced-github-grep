import requests
from argparse import ArgumentParser
import json
import re

NEWLINE_REPLACE_PATTERN = re.compile(r"\s*\n\s*", re.MULTILINE)

def parse_args():
    parser = ArgumentParser()
    group = parser.add_argument_group("Filtering options", "Options passed to grep.app")
    # Filtering options
    group.add_argument("filter_pattern", help="String or regex (-r flag) to pre-filter files using grep.app")
    group.add_argument("-i", "--filter-ignore-case", action="store_true", help="Should the filter String/Regex be case-sensitive")
    group.add_argument("-r", "--regex-filter", action="store_true", help="Set this flag if filter_pattern is a regex")
    group.add_argument("-w", "--whole-words", action="store_true", help="Equivalent to the whole-words flag on grep.app")
    # Regex options
    parser.add_argument("pattern", nargs="?", help="Regex pattern to search through the filtered results.")
    parser.add_argument("-f", "--pattern_file", help="File containing the pattern (use instead of pattern)")
    parser.add_argument("-m", "--multiline", action="store_true", help="re.MULTILINE flag")
    parser.add_argument("-I", "--ignore-case", action="store_true", help="re.IGNORECASE flag")
    parser.add_argument("-s", "--ignore-spaces", action="store_true", help="Ignore spaces and newlines inside the regex pattern")
    parser.add_argument("-p", "--page-count", type=int, default=1, help="Number of pages to request")
    parser.add_argument("-o", "--page-offset", type=int, default=0, help="First page to request")
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
        "current": page,
        "filter[lang][0]": "PHP"
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
    results = [x if type(x) == str else x[0] for x in results]
    results = [x for x in results if "$_" in x]
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

    # Pattern options
    if args.pattern_file:
        with open(args.pattern_file, "r") as fp:
            args.pattern = fp.read()
    if args.ignore_spaces:
        args.pattern = args.pattern.replace(" ", "").replace("\n", "")
    print("Pattern:", args.pattern)
    regex_options = []
    if args.multiline:
        regex_options.append(re.MULTILINE)
    if args.ignore_case:
        regex_options.append(re.IGNORECASE)
    pattern = re.compile(args.pattern, *regex_options)

    # Run
    page = args.page_offset
    while True:
        data = get_filtered_data_paginated(args.filter_pattern, args.filter_ignore_case, args.regex_filter, args.whole_words, page)
        for entry in data["hits"]["hits"]:
            repo = entry["repo"]["raw"]
            path = entry["path"]["raw"]

            file_content = get_complete_file(repo, path)
            result = search(file_content, pattern)
            print_findings(args, repo, path, result)

        

        page += 1

        if page >= args.page_count:
            break
