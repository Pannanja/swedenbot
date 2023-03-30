import re

#NCBS text formatting

def format_text(text, book_name):
    # if book_name == "Swedenborg Dot Com":
    #     print("Swedenborg.com file detected")
    #     references, content = format_text_from_swedenborg_dot_com(text, book_name)
    # else:
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

def format_text_from_swedenborg_dot_com(text, book_name): #Outdated, isn't used
    
    markup_new_section = r"###(.*?)###"
    markup_new_subsection = r"@@@(.*?)@@@"

    def clean(): #Removes formatting
        content[-1] = re.sub(markup_new_section,"",content[-1])
        content[-1] = re.sub(markup_new_subsection,"",content[-1])


    references = [""]
    content = [""]

    reference_markup = ""
    subsection_number = "" #Defaults to [1] when a new section starts

    text_file_lines = re.split("\n\n", text)


    #Content formatting, (reference gets formatted a little)

    for i, line in enumerate(text_file_lines):

        #Checks for new section

        if re.search(markup_new_section, line):
            subsection_number = ""

            reference_markup = re.search(markup_new_section, line).group()
            references.append(reference_markup[:-1])

            content.append(line)
        
        #Checks for new subsection

        elif re.search(markup_new_subsection, line):
            subsection_number = re.search(markup_new_subsection, line).group()

            references.append(reference_markup[:-1] + subsection_number)

            content.append(line)
        
        else:
            content[-1] += "\n\n" + line
        
        clean()
    for i, item in enumerate(references):

        references[i] = book_name + " " + references[i]


    return references, content