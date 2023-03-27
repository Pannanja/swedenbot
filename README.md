# swedenbot
A language learning model that can respond to questions about Emanuel Swedenborg's books with references

Code is still in progress, I apologize for any vague comments.

You need an API token from OpenAI. Put it into a ".env" file with this format:

api-token = "insert-token-here"

The script will check to see if there are any books that haven't been embedded yet. Embedded files are in the "data" folder, and books are in the "books" folder.

Then, you can ask Swedenbot questions!

He will give his response, then will return the 5 passages used to formulate the response. He has only read those 5 passages, will update in the future to give him more info!
