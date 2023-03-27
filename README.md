# swedenbot
A language learning model that can respond to questions about Emanuel Swedenborg's books with references.

You need an API token from OpenAI. Put it into a ".env" file with this format:

api-token = "insert-token-here"

Put .txt files from New Christian Bible Study (with markups) into the "books" folder. Run the "swedenbot.py" file.

Then, you can ask Swedenbot questions!

He will give his response, then will return the passages used to formulate the response. 

I'm still learning python and github! I apologize in advance for bad practices or mistakes.

Possible Todos:

-Ask follow up questions
-Allow for non-NCBS sources, like blogs
-Smaller embeds (individual sentances) that goes alongside the larger embedding
-Add feedback system (If possible)
-Use ChatGTP created summaries to further teach Swedenbot
-Have Swedenbot highlight suggested passages