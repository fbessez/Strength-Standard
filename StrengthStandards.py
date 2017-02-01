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
    XP_level = master_table[gender][0][len(weights) - 1]
    return [XP_level, weights[-1]]

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
        XP_and_GOAL = find_match(table, gender, user_weight, user_one_rep_max)
        result = "You are currently %s at %s. The next class will be achieved at a one rep max of %i %s" % (XP_conversion[XP_and_GOAL[0]], exercise, XP_and_GOAL[1], metric)
        return result
    except:
        print("Here's a list of all the approved exercises: %s" % acceptable_exercises)
        return

# An example of what p.tables would look like
# x = [[['BW', 'Beg.', 'Nov.', 'Int.', 'Adv.', 'Elite'], 
# 	  ['120', '67 x0.56', '101 x0.84', '143 x1.19', '193 x1.61', '247 x2.06'], 
# 	  ['130', '77 x0.59', '112 x0.87', '157 x1.21', '209 x1.61', '265 x2.04'], 
# 	  ['140', '86 x0.62', '124 x0.89', '171 x1.22', '225 x1.6', '283 x2.02'], 
# 	  ['150', '96 x0.64', '135 x0.9', '184 x1.22', '240 x1.6', '300 x2'], 
# 	  ['160', '105 x0.66', '146 x0.91', '196 x1.23', '254 x1.59', '316 x1.97'], 
# 	  ['170', '114 x0.67', '157 x0.92', '209 x1.23', '268 x1.58', '332 x1.95'], 
# 	  ['180', '123 x0.68', '167 x0.93', '221 x1.23', '282 x1.56', '347 x1.93'], 
# 	  ['190', '132 x0.69', '177 x0.93', '232 x1.22', '295 x1.55', '361 x1.9'], 
# 	  ['200', '140 x0.7', '187 x0.94', '244 x1.22', '307 x1.54', '375 x1.88'], 
# 	  ['210', '149 x0.71', '197 x0.94', '255 x1.21', '320 x1.52', '389 x1.85'], 
# 	  ['220', '157 x0.71', '206 x0.94', '265 x1.21', '332 x1.51', '402 x1.83'], 
# 	  ['230', '165 x0.72', '216 x0.94', '276 x1.2', '343 x1.49', '415 x1.8'], 
# 	  ['240', '173 x0.72', '225 x0.94', '286 x1.19', '355 x1.48', '427 x1.78'], 
# 	  ['250', '181 x0.72', '233 x0.93', '296 x1.18', '366 x1.46', '439 x1.76'], 
# 	  ['260', '188 x0.72', '242 x0.93', '306 x1.18', '377 x1.45', '451 x1.74'], 
# 	  ['270', '196 x0.72', '250 x0.93', '315 x1.17', '387 x1.43', '463 x1.71'], 
# 	  ['280', '203 x0.73', '259 x0.92', '324 x1.16', '397 x1.42', '474 x1.69'], 
# 	  ['290', '210 x0.72', '267 x0.92', '333 x1.15', '407 x1.41', '485 x1.67'], 
# 	  ['300', '217 x0.72', '275 x0.92', '342 x1.14', '417 x1.39', '496 x1.65'], 
# 	  ['310', '224 x0.72', '283 x0.91', '351 x1.13', '427 x1.38', '506 x1.63']], 
# 	 [['BW', 'Beg.', 'Nov.', 'Int.', 'Adv.', 'Elite'], 
# 	  ['100', '23 x0.23', '46 x0.46', '79 x0.79', '120 x1.2', '168 x1.68'], 
# 	  ['110', '27 x0.24', '51 x0.47', '86 x0.78', '129 x1.17', '178 x1.62'], 
# 	  ['120', '31 x0.25', '57 x0.47', '92 x0.77', '137 x1.14', '188 x1.56'], 
# 	  ['130', '34 x0.26', '62 x0.47', '99 x0.76', '145 x1.11', '197 x1.51'], 
# 	  ['140', '38 x0.27', '66 x0.47', '105 x0.75', '152 x1.08', '205 x1.46'], 
# 	  ['150', '41 x0.28', '71 x0.47', '110 x0.74', '159 x1.06', '213 x1.42'], 
# 	  ['160', '45 x0.28', '75 x0.47', '116 x0.72', '165 x1.03', '221 x1.38'], 
# 	  ['170', '48 x0.28', '80 x0.47', '121 x0.71', '172 x1.01', '228 x1.34'], 
# 	  ['180', '51 x0.28', '84 x0.47', '126 x0.7', '178 x0.99', '235 x1.3'], 
# 	  ['190', '54 x0.29', '88 x0.46', '131 x0.69', '184 x0.97', '242 x1.27'], 
# 	  ['200', '57 x0.29', '92 x0.46', '136 x0.68', '189 x0.95', '248 x1.24'], 
# 	  ['210', '60 x0.29', '95 x0.45', '141 x0.67', '195 x0.93', '254 x1.21'], 
# 	  ['220', '63 x0.29', '99 x0.45', '145 x0.66', '200 x0.91', '260 x1.18'], 
# 	  ['230', '66 x0.29', '103 x0.45', '149 x0.65', '205 x0.89', '266 x1.16'], 
# 	  ['240', '69 x0.29', '106 x0.44', '154 x0.64', '210 x0.87', '272 x1.13'], 
# 	  ['250', '72 x0.29', '110 x0.44', '158 x0.63', '215 x0.86', '277 x1.11'], 
# 	  ['260', '74 x0.29', '113 x0.43', '162 x0.62', '219 x0.84', '282 x1.09']]]

