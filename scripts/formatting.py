import re

#NCBS text formatting

def format_text(text, book_name):
    references, content = format_text_from_ncbs(text, book_name)
    return references, content

def format_text_from_ncbs(text, book_name):
    text_file_lines = re.split("\n", text)

    references = []
    content = []

    markups = { #Format is 'Markup Type' : (compiled regex, what to replace it with)
        'New Section' : (re.compile(r'ppp\d+#pid#(\d+). '), ""),
        'New Subsection' : (re.compile(r'ttt\[(\d+)\] '), ""),
        'New Book' : (re.compile(r'\d+#pid#(\d+). '), ""),
        'New Item List' : (re.compile(r"`fff(\d+)`"), ""),
        'New Reference' : ("@@@", ""),
        'New Reference_1' : ("bbbccc", ":"),
        'New Reference_2' : ("bbb", ":"),
        'New Reference_3' : ("ccc", ":"),
    }
    
    current_section = 1
    current_subsection = 1
    new_content = ""

    for i, item in enumerate(text_file_lines):
        if item != "":
            if markups["New Section"][0].search(item) or markups["New Book"][0].search(item) or markups["New Subsection"][0].search(item):
                references.append([book_name,current_section,current_subsection])
                for markup in markups:
                    regex_pattern, replacement_string = markups[markup]
                    new_content = re.sub(regex_pattern, replacement_string, new_content)
                content.append(new_content)
                new_content = item
                if markups["New Section"][0].search(item):
                    current_section = int(markups["New Section"][0].search(item).group(1))
                    current_subsection = 1
                if markups["New Book"][0].search(item):
                    current_section = int(markups["New Book"][0].search(item).group(1))
                    current_subsection = 1
                if markups["New Subsection"][0].search(item):
                    current_subsection = int(markups["New Subsection"][0].search(item).group(1))
            else:
                new_content += item
        else:
            new_content += "\n\n"
    return references, content    