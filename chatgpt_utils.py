import openai
import time
import traceback

from ds.gpt3_key_manager import get_gpt3_key
from generation_app.testing.slack_hook import send_msg_to_slack

class ChatGptGenerator: 
    def __init__(self) -> None:
        pass

    def generate(self, prompt: list, **kwargs):
        start_time = time.time()
        response = openai.ChatCompletion.create(
            messages=prompt,
            model=kwargs.get("model", "gpt-3.5-turbo"), 
            temperature=kwargs.get("temperature", 0.7), 
            max_tokens=kwargs.get("response_length", 500), 
            top_p=kwargs.get("top_p", 1), 
            frequency_penalty=kwargs.get("frequency_penalty", 0), 
            presence_penalty=kwargs.get("presence_penalty", 0), 
            stop=kwargs.get("stop", ''),
            n = kwargs.get("n", 1)
        )
        print('ChatGPT Call took {} seconds'.format(time.time() - start_time))
        output = []
        for choice in response['choices']:
            ## Discard the last sentence from the responce text
            if choice['finish_reason'] == 'length':
                output.append('\n'.join(choice['message']['content'].split('\n')[:-1]))
            else:
                output.append(choice['message']['content'])

        return output, response 

    def execute(self,prompt: list, **kwargs) -> list:
        try:
            openai.api_key, openai.organization = get_gpt3_key()
            output, response = self.generate(prompt=prompt, **kwargs)
            return output, response
        except:
            try:
                openai.api_key, openai.organization = get_gpt3_key(rotate=True)
                output, response = self.generate(prompt=prompt, **kwargs)
                return output, response
            except Exception as e:
                tb = traceback.format_exc()
                send_msg_to_slack(str(e),tb)
                raise e
