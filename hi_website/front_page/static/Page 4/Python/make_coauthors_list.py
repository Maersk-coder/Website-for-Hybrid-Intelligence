# PAGE 4 · MAKE THE CO-AUTHORS LIST
# Reads the co-authors from Data/coauthors.csv and writes JS/coauthors_list.js,
# which the co-authors pop-up on the page uses.
# (When Django is set up, this script isn't needed anymore.)
#
# HOW TO CHANGE THE CO-AUTHORS LIST
#   1. Edit Data/coauthors.csv: one line per person, in the order they should appear: name;role;place
#        Example:  Jane Doe;Assoc. Prof.;Aarhus University
#        - In VS Code: keep the ";" between the three parts.
#        - In Excel: save as "CSV UTF-8", or letters like æ, ø, å, ö can get scrambled.
#   2. Run this script. In the VS Code terminal, from the "Hybrid Intelligence" folder:
#        python "hi_website/front_page/static/Page 4/Python/make_coauthors_list.py"
#      It prints e.g. "Done: 62 co-authors written to coauthors_list.js".
#      (Tip: the up arrow key in the terminal brings back the last command.)
#   3. Refresh the page with Ctrl + F5 and open the Co-authors pop-up.
#
#   Forget step 2, and the page still shows the old list: the browser only reads coauthors_list.js, never the CSV.
#   Never edit coauthors_list.js by hand: this script overwrites it every time it runs.

import csv
import json 
from pathlib import Path

# Where the files are. Worked out from where THIS script is, so it works no matter which folder you run it from.
page_4 = Path(__file__).parent.parent     # this file is placed in "page 4/python"
csv_file = page_4 / "Data" / "coauthors.csv"
js_file = page_4 / "JS" / "coauthors_list.js"

# 1. Read the CSV. Each row becomes a "dictionary": {"name": "...", "role": "...", "place": "..."}
with open(csv_file, encoding="utf-8-sig", newline="") as f:    # utf-8-sig reads æ, ø, å correctly, also after Excel
    coauthors = list(csv.DictReader(f, delimiter=";"))        # ";" because that's what separates the columns

coauthors = [person for person in coauthors if person["name"].strip()]  #Skips empty rows

# 2. Turn each co-author into one line of Javascript
lines = []
for person in coauthors:
    lines.append(" " + json.dumps(person, ensure_ascii=False) + ",") # ensure_ascii = False keeps æ,ø,å (danish letters)


# 3. Write the JavaScript file
js_text = (
    "// MADE BY Python/make_coauthors_list.py FROM Data/coauthors.csv. Don't edit by hand:\n"
    "// change the CSV and run the script again.\n\n"
    "const COAUTHORS = [\n" + "\n".join(lines) + "\n];\n"
)
js_file.write_text(js_text, encoding="utf-8")

print(f"Done: {len(coauthors)} co-authors written to {js_file.name}")

