#### Author: Fabien Bessez
#### Purpose: This program scrapes data from strengthlevel.com
####          and organizes it in such a way that allows a user
####          to compare the user's current weight lifting PRs
####          with others'.

import urllib.request
import re
from html.parser import HTMLParser

# http://strengthlevel.com/strength-standards

# The HTMLTableParser class source: https://github.com/schmijos/html-table-parser-python3

class HTMLTableParser(HTMLParser):
    """ This class serves as a html table parser. It is able to parse multiple
    tables which you feed in. You can access the result per .tables field.
    """
    def __init__(
        self,
        decode_html_entities=False,
        data_separator=' ',
    ):

        HTMLParser.__init__(self)

        self._parse_html_entities = decode_html_entities
        self._data_separator = data_separator

        self._in_td = False
        self._in_th = False
        self._current_table = []
        self._current_row = []
        self._current_cell = []
        self.tables = []

    def handle_starttag(self, tag, attrs):
        """ We need to remember the opening point for the content of interest.
        The other tags (<table>, <tr>) are only handled at the closing point.
        """
        if tag == 'td':
            self._in_td = True
        if tag == 'th':
            self._in_th = True

    def handle_data(self, data):
        """ This is where we save content to a cell """
        if self._in_td or self._in_th:
            self._current_cell.append(data.strip())

    def handle_charref(self, name):
        """ Handle HTML encoded characters """

        if self._parse_html_entities:
            self.handle_data(self.unescape('&#{};'.format(name)))

    def handle_endtag(self, tag):
        """ Here we exit the tags. If the closing tag is </tr>, we know that we
        can save our currently parsed cells to the current table as a row and
        prepare for a new row. If the closing tag is </table>, we save the
        current table and prepare for a new one.
        """
        if tag == 'td':
            self._in_td = False
        elif tag == 'th':
            self._in_th = False

        if tag in ['td', 'th']:
            final_cell = self._data_separator.join(self._current_cell).strip()
            self._current_row.append(final_cell)
            self._current_cell = []
        elif tag == 'tr':
            self._current_table.append(self._current_row)
            self._current_row = []
        elif tag == 'table':
            self.tables.append(self._current_table)
            self._current_table = []


base_url = "http://strengthlevel.com/strength-standards/"

acceptable_exercises = [
    "bench press", "deadlift", "squat", "shoulder press",
    "pull ups", "barbell curl", "dips", "front squat", 
    "bent over row", "power clean", "clean", "push press",
    "clean and jerk", "snatch", "clean and press"]

XP_conversion = {
    "Beg.": "Beginner",
    "Nov.": "Novice",
    "Int.": "Intermediate",
    "Adv.": "Advanced",
    "Elite": "Elite"
    }


# INPUT1: exercise : string --> see the global acceptable_exercises list
# INPUT2: metric : string --> either "lb" or "kg"
# OUTPUT: target : string --> represents the target URL to scrape
# Notes: Simple function that forms the correct endpoint
def get_target(exercise, metric):
    if exercise in acceptable_exercises:
        exercise = re.sub(r"\s+", '-', exercise)
        global base_url
        target = base_url + exercise + "/" + metric
        return target
    else:
        print("Data on", exercise, "is not available :(")
        print("Choose one of the following:", acceptable_exercises)
        return 

# INPUT1: target: string --> the target URL
# OUTPUT: p.tables : list of lists --> the list representation of the chart on 
#                                      the target URL. 
# Notes: Makes use of urllib to scrape the html as well as HTMLTableParser to 
#        convert the table into list format
def get_html_table(target): 
    try:
        req = urllib.request.Request(target)
        f = urllib.request.urlopen(req)
        xhtml = f.read().decode("utf-8")
        p = HTMLTableParser()
        p.feed(xhtml)
        return p.tables
        # x = p.tables[0] # Man
        # y = p.tables[1] # Woman
    except: 
        print("Data on", exercise, "is not available :(")
        return

# INPUT1: master_table : list of lists --> the p.tables that was returned
# INPUT2: gender: integer --> 0 for male and 1 for female
# INPUT3: user_weight: integer
# INPUT4: one_rep_max: integer --> the max weight that user can perform one rep
# OUTPUT: XP_level, WEIGHT : list --> 
#                           XP_level : string--> "Beg" or "Nov" or "Int" or "Adv" or "Elite"
#                           WEIGHT : int --> The weight at which user would enter the next class
def find_match(master_table, gender, user_weight, one_rep_max):
    user_weight = int(round(user_weight, -1))
    row_index = user_weight // 10 + 1 - 12
    row = master_table[gender][row_index]
    weights = []
    for entry in row[1:]:
        rep_weight = int(entry[:3])
        if rep_weight >= one_rep_max:
            weights.append(rep_weight)
            break
        weights.append(rep_weight)
    x = {"curr_lvl": master_table[gender][0][len(weights) - 1],
            "next_lvl": master_table[gender][0][len(weights)],
            "goal": weights[-1]}
    print(weights)
    return x

# INPUT1: exercise : string --> see the global acceptable_exercises list
# INPUT2: gender: integer --> 0 for male and 1 for female
# INPUT3: user_weight: integer
# INPUT4: one_rep_max: integer --> the max weight that user can perform one rep
# INPUT5: metric : string --> either "lb" or "kg". It defaults to "lb"
# OUTPUT: string --> states what class of weightlifting the user falls under 
def class_finder(exercise, gender, user_weight, user_one_rep_max, metric="lb"):
    target = get_target(exercise, metric)
    try: 
        table = get_html_table(target)
        response_dict = find_match(table, gender, user_weight, user_one_rep_max)
        if "sorry" not in response_dict:
            print("You are currently %s at %s" % (XP_conversion[response_dict["curr_lvl"]], exercise))
            print("To become %s, you need to hit a one rep max of %i %s" % (XP_conversion[response_dict["next_lvl"]], response_dict["goal"], metric))
        return
    except:
        if user_weight > 310 and gender == 0: 
            return "Sorry, we don't have data for your weight class. Max is 310 lbs."
        elif user_weight > 260 and gender == 1: 
            return "Sorry, we don't have data for your weight class. Max is 260 lbs."
        else:
            print("Here's a list of all the approved exercises:")
            print(*acceptable_exercises, sep="\n")
            return

# INPUT1: user_weight: integer
# INPUT2: one_rep_max: integer --> the max weight that user can perform one rep
# OUTPUT: weight_bw_ratio : float --> the ratio of weight lifted to body weight
def weight_bw_ratio(user_weight, user_one_rep_max):
    return user_one_rep_max / user_weight

if __name__ == "__main__":
    exercise = input('What exercise are you checking for? ')
    if exercise not in acceptable_exercises:
        print("That exercise does not exist. Next time choose one of the following: ", acceptable_exercises)
        exit(0)
    one_rep_max = int(input("What is your one rep max for %s? " % exercise))
    body_weight = int(input("What is your current body weight? "))
    metric = input("What is your desired weight metric? (lb/kg) ")
    gender = int(input("What is your gender? 0 for Male, 1 for Female "))
    htmlTable = get_html_table(get_target(exercise, metric))
    match = find_match(htmlTable, gender, body_weight, one_rep_max)
    print(match)






