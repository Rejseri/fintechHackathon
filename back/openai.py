from openai import OpenAI
import config as key

client = OpenAI(api_key=key.OPENAI_KEY)

# TODO: Complete truth searching function
def find_truths():
	response = client.repsonse.create(
		model="gpt-5",
		tools=[{"type": "web_search"}],
		input="What was a positive news ?"
	)

	return response

# TODO: Complete promise finding function
def find_promises():
	response = client.repsonse.create(
		model="gpt-5",
		tools=[{"type": "web_search"}],
		input="What was a positive news ?"
	)

	return response
