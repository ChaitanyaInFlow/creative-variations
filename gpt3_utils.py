import openai
import time
import traceback
from ds.gpt3_key_manager import get_gpt3_key
from generation_app.testing.slack_hook import send_msg_to_slack

class Gpt3Generator:
    def __init__(self):
        pass 
    
    def generate(self, prompt: str, **kwargs):
        start_time = time.time()
        n = kwargs.get("n", 1)
        response = openai.Completion.create(
            prompt=prompt,
            engine=kwargs.get("engine", "text-davinci-003"),
            max_tokens=kwargs.get("max_tokens", 256),
            temperature=kwargs.get("temperature", .7),
            top_p=kwargs.get("top_p", 1),
            frequency_penalty=kwargs.get("frequency_penalty", 0),
            presence_penalty=kwargs.get("presence_penalty", 0), 
            stop=kwargs.get("stop", ''), 
            n=n
            )
        print('GPT3 Call took {} seconds'.format(time.time() - start_time))
        output = []
        for choice in response['choices']:
            ## Discard the last sentence from the responce text
            if choice['finish_reason'] == 'length':
                output.append('\n'.join(choice['text'].split('\n')[:-1]))
            else:
                output.append(choice['text'])

        # [prompt1, prompt2, prompt3] --> outputs are concatenated [(1,2,3,4)  (5,6,7,8)   (9,10,11,12)]
        if type(prompt) == list:
            return ['\n'.join(output[idx:idx+n]) for idx in range(0,n*len(prompt),n)], response
        else:
            return output, response

    def execute(self, prompt: str, **kwargs) -> list:
        try:
            openai.api_key, openai.organization = get_gpt3_key()
            output, response = self.generate(prompt=prompt, **kwargs)
            return output, response
        except:
            try:
                time.sleep(3)
                openai.api_key, openai.organization = get_gpt3_key(rotate=True)
                output, response = self.generate(prompt=prompt, **kwargs)
                return output, response
            except Exception as e:
                tb = traceback.format_exc()
                send_msg_to_slack(str(e), tb + prompt)
                raise e


if __name__ == '__main__':
    print(Gpt3Generator().execute("tell a joke",stop="A:",n=10))