import re

#NCBS text formatting

def format_text(text, book_name):
    if book_name == "Swedenborg Dot Com":
        print("Swedenborg.com file detected")
        references, content = format_text_from_swedenborg_dot_com(text, book_name)
    else:
        references, content = format_text_from_ncbs(text, book_name)
    return references, content

def format_text_from_ncbs(text, book_name): #Sort of works. Not great. I'm planning to rewrite.

    markup_new_section = r'ppp\d+#pid#\d+.'
    markup_new_section_short = "#pid#"
    markup_new_subsection = r'ttt\[\d+\] '
    markup_bible_verse = 'bbb'
    markup_bible_verse_2 = 'bbbccc'
    markup_bible_verse_3 = 'ccc'
    markup_unknown = r"`fff\d+`"
    markup_unknown_2 = "`qqq`"
    markup_unknown_3 = "@@@"

    def clean(): #Removes formatting
        content[-1] = content[-1].replace(markup_unknown_3,"")
        content[-1] = content[-1].replace(markup_bible_verse,":")
        content[-1] = content[-1].replace(markup_bible_verse_2,":")
        content[-1] = content[-1].replace(markup_bible_verse_3,":")
        content[-1] = content[-1].replace(markup_unknown_2,"")
        content[-1] = content[-1].replace(markup_unknown_3,"")
        #content[-1] = re.sub(markup_new_section[:-1],"",content[-1])
        content[-1] = re.sub(markup_new_section,"",content[-1])
        content[-1] = re.sub(markup_new_subsection,"",content[-1])
        content[-1] = re.sub(markup_unknown,"",content[-1])

    references = [""]
    content = [""]

    reference_markup = ""
    subsection_number = "ttt[1]" #Defaults to [1] when a new section starts

    text_file_lines = re.split("\n\n", text)


    #Content formatting, (reference gets formatted a little)

    for i, line in enumerate(text_file_lines):

        #Checks for new section

        if re.search(markup_new_section, line):
            subsection_number = "ttt[1]"

            reference_markup = re.search(markup_new_section, line).group()
            references.append(reference_markup[:-1] + subsection_number)

            content.append(line)
        
        #Checks for new subsection

        elif re.search(markup_new_subsection, line):
            subsection_number = re.search(markup_new_subsection, line).group()

            references.append(reference_markup[:-1] + subsection_number)

            content.append(line)
        
        else:
            content[-1] += "\n\n" + line
        
        clean()

                    

    #Reference formatting

    for i, item in enumerate(references):

        reference_pid = references[i].find(markup_new_section_short)
        if reference_pid != -1:
            references[i] = references[i][reference_pid+len(markup_new_section_short):]
        
        references[i] = references[i].replace("ttt","")

        references[i] = book_name + " " + references[i]

    return references, content

def format_text_from_swedenborg_dot_com(text, book_name):
    
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